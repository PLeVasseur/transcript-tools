from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from .triage import load_groups, dump_groups, run_triage


def main(argv: Optional[list[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        prog="transcript-triage",
        description=(
            "Interactively reassign segments between grouped speakers and "
            "insert new speaker groups."
        ),
    )
    parser.add_argument(
        "input",
        type=Path,
        help="Path to the grouped JSON file (speaker + segments list).",
    )
    parser.add_argument(
        "output",
        type=Path,
        help="Path where the updated grouped JSON should be written.",
    )
    parser.add_argument(
        "--start-group",
        type=int,
        default=1,
        help=(
            "1-based index of the group at which to start triage. "
            "Defaults to 1 (the first group)."
        ),
    )

    args = parser.parse_args(argv)

    try:
        groups = load_groups(args.input)
        should_write = run_triage(groups, start_group=args.start_group)

        if not should_write:
            print("Quitting without writing any changes.")
            return

        dump_groups(args.output, groups)

    except Exception as exc:  # noqa: BLE001
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
