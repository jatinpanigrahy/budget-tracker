import pytest
from models import Category, InsufficientFundsError


def test_category_initialization():
    """Test that a Category is initialized with the correct name and an empty ledger."""
    cat = Category("Food")
    assert cat.name == "Food"
    assert len(cat.ledger) == 0
    assert cat.get_balance() == 0.0

def test_deposit_valid_amount():
    """Test that a valid deposit updates the ledger and balance correctly."""
    cat = Category("Food")
    cat.deposit(100.50, "Groceries")
    
    assert cat.get_balance() == 100.50
    assert len(cat.ledger) == 1
    
    entry = cat.ledger[0]
    assert entry["amount"] == 100.50
    assert entry["description"] == "Groceries"
    assert "timestamp" in entry

def test_deposit_invalid_amount():
    """Test that depositing a zero or negative amount raises a ValueError."""
    cat = Category("Food")
    with pytest.raises(ValueError):
        cat.deposit(0)
    with pytest.raises(ValueError):
        cat.deposit(-50)

def test_withdraw_valid_amount():
    """Test that a valid withdrawal correctly reduces the balance."""
    cat = Category("Food")
    cat.deposit(200, "Initial")
    cat.withdraw(50, "Dinner")
    
    assert cat.get_balance() == 150.0
    assert len(cat.ledger) == 2
    
    withdraw_entry = cat.ledger[1]
    assert withdraw_entry["amount"] == -50.0
    assert withdraw_entry["description"] == "Dinner"

def test_withdraw_insufficient_funds():
    """Test that withdrawing more than the available balance raises InsufficientFundsError."""
    cat = Category("Food")
    cat.deposit(100, "Initial")
    
    with pytest.raises(InsufficientFundsError):
        cat.withdraw(150, "Dinner")
        
    assert cat.get_balance() == 100.0
    assert len(cat.ledger) == 1

def test_withdraw_invalid_amount():
    """Test that withdrawing a zero or negative amount raises a ValueError."""
    cat = Category("Food")
    cat.deposit(100, "Initial")
    
    with pytest.raises(ValueError):
        cat.withdraw(0)
    with pytest.raises(ValueError):
        cat.withdraw(-20)

def test_transfer_success():
    """Test that funds are successfully transferred between two categories."""
    food = Category("Food")
    entertainment = Category("Entertainment")
    
    food.deposit(500, "Initial")
    food.transfer(100, entertainment)
    
    assert food.get_balance() == 400.0
    assert entertainment.get_balance() == 100.0
    
    assert food.ledger[-1]["amount"] == -100.0
    assert "Transfer to Entertainment" in food.ledger[-1]["description"]
    
    assert entertainment.ledger[-1]["amount"] == 100.0
    assert "Transfer from Food" in entertainment.ledger[-1]["description"]

def test_transfer_insufficient_funds():
    """Test that a transfer fails safely if the source category has insufficient funds."""
    food = Category("Food")
    entertainment = Category("Entertainment")
    
    food.deposit(50, "Initial")
    
    with pytest.raises(InsufficientFundsError):
        food.transfer(100, entertainment)
        
    assert food.get_balance() == 50.0
    assert entertainment.get_balance() == 0.0

def test_check_funds():
    """Test the check_funds helper method."""
    cat = Category("Food")
    cat.deposit(100, "Initial")
    
    assert cat.check_funds(50) is True
    assert cat.check_funds(100) is True
    assert cat.check_funds(100.01) is False
