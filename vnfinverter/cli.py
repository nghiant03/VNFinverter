import argparse
from pathlib import Path
from vnfinverter.parser import parse_pdf
from vnfinverter.converter import to_ofx

def main():
    parser = argparse.ArgumentParser(description="VNFinverter")
    parser.add_argument("--path", help="Path to PDF", required=True)
    parser.add_argument("--out", help="Output file path", required=True)
    args = parser.parse_args()

    statement = parse_pdf(Path(args.path))
    ofx_content = to_ofx(statement)

    with open(args.out, "wb") as f:
        f.write(ofx_content)

if __name__ == "__main__":
    main()
