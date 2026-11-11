"""Run the FX forecasting and VaR analysis from the repository root."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from fxrisk.cli import main

if __name__ == "__main__":
    main()
