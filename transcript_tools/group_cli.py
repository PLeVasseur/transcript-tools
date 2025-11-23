from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from .grouping import group_consecutive_segments_file


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="transcript-group",
        description=(
            "Group consecutive segments from a slimmed transcript JSON by speaker. "
            "Produces segments like {speaker, segments: [utterance1, utterance2]}."
        ),
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the *slimmed* input JSON file.",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Path where the grouped JSON will be written.",
    )

    args = parser.parse_args(argv)

    try:
        group_consecutive_segments_file(
            input_path=args.input,
            output_path=args.output,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
