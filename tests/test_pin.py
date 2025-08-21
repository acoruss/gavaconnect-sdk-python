from gavaconnect import checkers


def test_kra_pin_checker_valid():
    checker = checkers.KRAPINChecker("123456")
    assert checker.check_by_id_number() == "Valid KRA PIN."


def test_kra_pin_checker_invalid():
    checker = checkers.KRAPINChecker("12345")
    assert checker.check_by_id_number() == "Invalid KRA PIN."
