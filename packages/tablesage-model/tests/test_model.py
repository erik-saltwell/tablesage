from tablesage_model import hello_model


def test_hello_model() -> None:
    assert hello_model() == "Hello from tablesage-model!"
