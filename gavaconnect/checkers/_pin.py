"""KRA PIN validation utilities."""

import re


class KRAPINChecker:
    """Checker for KRA PIN with improved validation."""

    def __init__(self, id_number: str | None) -> None:
        """Initialize with ID number for PIN validation.

        Args:
            id_number: The ID number to validate as KRA PIN.

        """
        self.id_number = id_number.strip() if id_number is not None else ""

    def check_by_id_number(self) -> str:
        """Validate KRA PIN format and content.

        Returns:
            Validation result message.

        """
        if not self.id_number:
            return "Invalid KRA PIN: Empty value."

        # Remove any whitespace
        pin = self.id_number.strip()

        # Check basic length requirement
        if len(pin) != 6:
            return "Invalid KRA PIN: Must be exactly 6 characters."

        # Check if contains only alphanumeric characters (typical for KRA PINs)
        if not re.match(r"^[A-Za-z0-9]{6}$", pin):
            return "Invalid KRA PIN: Must contain only alphanumeric characters."

        # Additional validation: KRA PINs typically start with letter
        if not pin[0].isalpha():
            return "Invalid KRA PIN: Must start with a letter."

        return "Valid KRA PIN."
