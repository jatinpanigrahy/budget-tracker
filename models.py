import datetime

class InsufficientFundsError(Exception):
    """Raised when a withdrawal or transfer exceeds the available balance."""
    pass


class Category:
    """
    Represents a financial category ledger.
    
    Maintains a record of deposits, withdrawals, and transfers, 
    ensuring strict data integrity by preventing negative amounts 
    and overdrafts.
    """

    def __init__(self, name: str):
        """
        Initializes a new Category.

        Args:
            name (str): The name of the budget category.
        """
        self.name = name
        self.ledger = []

    def deposit(self, amount: float, description: str = "") -> None:
        """
        Adds funds to the category ledger.

        Args:
            amount (float): The amount to deposit. Must be strictly positive.
            description (str, optional): A description of the transaction. Defaults to "".

        Raises:
            ValueError: If the amount is zero or negative.
        """
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Deposit amount must be strictly positive.")

        self.ledger.append({
            "amount": amount,
            "description": description,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def withdraw(self, amount: float, description: str = "") -> None:
        """
        Removes funds from the category ledger.

        Args:
            amount (float): The amount to withdraw. Must be strictly positive.
            description (str, optional): A description of the transaction. Defaults to "".

        Raises:
            ValueError: If the amount is zero or negative.
            InsufficientFundsError: If the withdrawal amount exceeds the current balance.
        """
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Withdrawal amount must be strictly positive.")

        if not self.check_funds(amount):
            raise InsufficientFundsError(f"Insufficient funds in {self.name} for this withdrawal.")

        self.ledger.append({
            "amount": -amount,
            "description": description,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })

    def get_balance(self) -> float:
        """
        Calculates the current balance of the category.

        Returns:
            float: The sum of all transactions in the ledger.
        """
        return sum(entry["amount"] for entry in self.ledger)

    def transfer(self, amount: float, receiver: 'Category') -> None:
        """
        Transfers funds from this category to another.

        Args:
            amount (float): The amount to transfer. Must be strictly positive.
            receiver (Category): The destination category.

        Raises:
            ValueError: If the amount is zero or negative.
            InsufficientFundsError: If there are not enough funds to transfer.
        """
        # withdraw will raise ValueError or InsufficientFundsError if invalid
        self.withdraw(amount, f"Transfer to {receiver.name}")
        receiver.deposit(amount, f"Transfer from {self.name}")

    def check_funds(self, amount: float) -> bool:
        """
        Checks if the category has enough funds for a given amount.

        Args:
            amount (float): The amount to check against the balance.

        Returns:
            bool: True if sufficient funds exist, False otherwise.
        """
        return float(amount) <= self.get_balance()
