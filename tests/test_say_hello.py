from hello_world.custom_functions import say_hello


def test_say_hello_returns_greeting() -> None:
    assert say_hello("Jonas") == "Hello, Jonas!"
