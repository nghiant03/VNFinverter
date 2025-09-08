import argparse
from pathlib import Path

import typer

from vnfinverter.converter import to_ofx
from vnfinverter.parser import parse_pdf

app = typer.Typer(help="VNFinverter CLI", no_args_is_help=True)

@app.command()
def main(input_path: Path, out_path: Path) -> int:
    statement = parse_pdf(input_path)
    ofx_content = to_ofx(statement)

    with open(out_path, "wb") as f:
        f.write(ofx_content)

    return 0 
