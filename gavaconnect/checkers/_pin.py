class KRAPINChecker:
    """Checker for KRA PIN."""

    def __init__(self, id_number: str) -> None:
        self.id_number = id_number

    def check_by_id_number(self) -> str:
        if len(self.id_number) == 6:
            return "Valid KRA PIN."
        return "Invalid KRA PIN."
