from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

from .segments import transform_segments_file


def _parse_speaker_map_arg(arg: Optional[str]) -> Any:
    """
    Parse the --speaker-map argument, which is expected to be a JSON string.

    This can be:
      - A JSON object: {"SPEAKER_01": "Xander Cesari", ...}
      - A JSON list of mapping objects (see `_normalize_speaker_map`).
    """
    if arg is None:
        return None

    try:
        return json.loads(arg)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"Error: --speaker-map must be valid JSON. "
            f"Received: {arg!r}\nDetails: {exc}"
        )


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="transcript-slim",
        description=(
            "Slim transcript JSON into segments containing only 'text' and "
            "'speaker', with optional speaker name mapping."
        ),
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Path to the input JSON file (with top-level 'segments' list).",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Path where the output JSON will be written.",
    )
    parser.add_argument(
        "--speaker-map",
        metavar="JSON",
        type=str,
        help=(
            "Optional JSON value describing an array/dict of speaker mappings. "
            "Examples:\n"
            "  '{\"SPEAKER_00\": \"Alice Jones\", \"SPEAKER_01\": \"Bob Smith\"}'\n"
            "  '[{\"SPEAKER_00\": \"Alice Jones\"}, {\"SPEAKER_01\": \"Bob Smith\"}]'\n"
        ),
    )

    args = parser.parse_args(argv)

    speaker_map_raw = _parse_speaker_map_arg(args.speaker_map)

    try:
        transform_segments_file(
            input_path=args.input,
            output_path=args.output,
            speaker_map_raw=speaker_map_raw,
        )
    except Exception as exc:  # noqa: BLE001
        # Simple CLI; just show the error and non-zero exit.
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
