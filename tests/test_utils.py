import json
import pytest
from models import Category
from utils import export_ledger, import_ledger


def test_export_ledger():
    """Test that export_ledger correctly serializes a dictionary of Categories."""
    food = Category("Food")
    food.deposit(100.50, "Groceries")
    food.withdraw(20.0, "Snacks")
    
    categories = {"Food": food}
    json_str = export_ledger(categories)
    
    # Parse back natively to verify exact structure
    data = json.loads(json_str)
    
    assert "categories" in data
    assert len(data["categories"]) == 1
    
    cat_data = data["categories"][0]
    assert cat_data["name"] == "Food"
    assert len(cat_data["ledger"]) == 2
    
    assert cat_data["ledger"][0]["amount"] == 100.50
    assert cat_data["ledger"][0]["description"] == "Groceries"
    assert cat_data["ledger"][1]["amount"] == -20.0
    assert cat_data["ledger"][1]["description"] == "Snacks"


def test_import_ledger_success():
    """Test that import_ledger deserializes JSON and perfectly preserves historical timestamps."""
    mock_json = json.dumps({
        "categories": [
            {
                "name": "Transport",
                "ledger": [
                    {"amount": 200.0, "description": "Initial", "timestamp": "2026-01-01T10:00:00Z"},
                    {"amount": -30.0, "description": "Gas", "timestamp": "2026-01-02T14:30:00Z"}
                ]
            }
        ]
    })
    
    restored = import_ledger(mock_json)
    
    assert "Transport" in restored
    transport_cat = restored["Transport"]
    assert isinstance(transport_cat, Category)
    
    # Verify the domain logic uses the restored ledger correctly
    assert transport_cat.get_balance() == 170.0
    assert len(transport_cat.ledger) == 2
    
    # Verify that the direct ledger assignment prevented timestamp overwriting
    assert transport_cat.ledger[0]["timestamp"] == "2026-01-01T10:00:00Z"
    assert transport_cat.ledger[1]["timestamp"] == "2026-01-02T14:30:00Z"


def test_import_ledger_invalid_json():
    """Test that importing corrupted JSON strings raises a ValueError."""
    bad_json = "{ invalid_json: this will fail"
    
    with pytest.raises(ValueError, match="Invalid JSON format."):
        import_ledger(bad_json)


def test_import_ledger_invalid_schema():
    """Test that importing valid JSON with an unexpected schema raises a ValueError."""
    # Missing the required 'categories' root key
    wrong_schema_json = json.dumps({
        "budget_data": [{"name": "Food", "ledger": []}]
    })
    
    with pytest.raises(ValueError, match="Invalid ledger schema: missing 'categories' key."):
        import_ledger(wrong_schema_json)
