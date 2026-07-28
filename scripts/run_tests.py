import subprocess


def main() -> None:
    """Run the tests."""

    subprocess.run(["poetry", "run", "pytest"], check=True)


if __name__ == "__main__":
    main()
