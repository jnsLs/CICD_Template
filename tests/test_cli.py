import pytest

from cicd_template.cli import build_message, main


def test_build_message_contains_text() -> None:
    # The rendered cow should embed the speech-bubble text.
    assert "Hello, world!" in build_message("Hello, world!")


def test_build_message_default_text() -> None:
    assert "Hello Pixi fans!" in build_message()


def test_main_prints_message(capsys: pytest.CaptureFixture[str]) -> None:
    main()
    assert "Hello Pixi fans!" in capsys.readouterr().out
