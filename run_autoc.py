"""Entry point for the packaged .exe (absolute import: works as a plain script)."""
from autoc.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
