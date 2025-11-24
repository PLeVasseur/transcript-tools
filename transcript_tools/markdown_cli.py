from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from .markdown_export import export_markdown_from_json


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="transcript-md",
        description=(
            "Convert a triaged/grouped transcript JSON into a markdown transcript "
            "with **speaker names** followed by concatenated segments."
        ),
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the triaged/grouped JSON file.",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Path where the markdown file should be written.",
    )

    args = parser.parse_args(argv)

    try:
        export_markdown_from_json(args.input, args.output)
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
