import json
from models import Category


def export_ledger(categories: dict[str, Category]) -> str:
    """
    Serializes the current financial state into a JSON string.

    Args:
        categories (dict[str, Category]): A dictionary mapping category names to Category instances.

    Returns:
        str: A JSON-formatted string representing the entire ledger state.
    """
    data = {"categories": []}

    for category in categories.values():
        cat_data = {
            "name": category.name,
            "ledger": category.ledger
        }
        data["categories"].append(cat_data)

    return json.dumps(data, indent=2)


def import_ledger(json_string: str) -> dict[str, Category]:
    """
    Deserializes a JSON string into a dictionary of Category instances.

    Args:
        json_string (str): The JSON-formatted string containing the ledger state.

    Returns:
        dict[str, Category]: A dictionary mapping category names to the reconstructed Category instances.

    Raises:
        ValueError: If the JSON string is invalid or does not match the expected schema.
    """
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        raise ValueError("Invalid JSON format.") from e

    if not isinstance(data, dict) or "categories" not in data:
        raise ValueError("Invalid ledger schema: missing 'categories' key.")

    restored_categories = {}

    for cat_data in data.get("categories", []):
        name = cat_data.get("name")
        if not name:
            continue

        category = Category(name)
        
        # Directly restore the ledger list to preserve the original 
        # timestamps and exact historical state.
        ledger_data = cat_data.get("ledger", [])
        if isinstance(ledger_data, list):
            category.ledger = ledger_data

        restored_categories[name] = category

    return restored_categories
