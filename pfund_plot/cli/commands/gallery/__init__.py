import sys
import subprocess
from pathlib import Path

import click

GALLERY_DIR = Path(__file__).parent


@click.command(hidden=True)
def gallery():
    """Open the gallery to visually verify all supported plots."""
    script = GALLERY_DIR / "gallery_marimo.py"
    result = subprocess.run(['marimo', 'edit', str(script)], check=False)
    sys.exit(result.returncode)