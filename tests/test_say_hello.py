from cicd_template.custom_functions import say_goodbye, say_hello, say_how_are_you


def test_say_hello_returns_greeting() -> None:
    assert say_hello("Jonas") == "Hello, Jonas!"


def test_say_goodbye_returns_farewell() -> None:
    assert say_goodbye("Jonas") == "Goodbye, Jonas!"


def test_say_how_are_you_returns_question() -> None:
    assert say_how_are_you("Jonas") == "How are you, Jonas?"
