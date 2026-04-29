from __future__ import annotations

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "code"

SCRIPTS = [
    CODE / "generate_analytical_workflow_figure.py",
    CODE / "generate_figure2_3_context_wrr.py",
    CODE / "generate_figure4_wrr.py",
    CODE / "generate_figure5_wrr.py",
    CODE / "generate_figure6_wrr.py",
    CODE / "generate_figure7_wrr.py",
]


def main() -> None:
    for script in SCRIPTS:
        subprocess.run([sys.executable, str(script)], check=True)


if __name__ == "__main__":
    main()
