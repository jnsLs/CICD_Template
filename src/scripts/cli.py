from cowpy.cow import Cowacter


def build_message(text: str = "Hello Pixi fans!") -> str:
    """Return the given text rendered as ASCII cow art."""
    return Cowacter().milk(text)


def main() -> None:
    print(build_message())


if __name__ == "__main__":
    main()
