from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Mapping, List


def _load_groups_from_json(path: Path) -> List[Mapping[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    segments = data.get("segments")
    if not isinstance(segments, list):
        raise ValueError(
            f"Expected top-level key 'segments' containing a list; "
            f"got {type(segments)!r}"
        )

    # We just trust items to be mapping-like; validation happens later.
    return segments


def _concat_group_segments(raw_segments: Iterable[str]) -> str:
    """
    Normalize and concatenate a group's segments into a single string.

    - Strip leading/trailing whitespace on each segment
    - Drop empty segments
    - Join with a single space
    """
    cleaned = [s.strip() for s in raw_segments if isinstance(s, str) and s.strip()]
    return " ".join(cleaned)


def export_markdown_from_json(input_path: Path, output_path: Path) -> None:
    """
    Read a triaged/grouped JSON file and produce a markdown transcript where
    each group is a paragraph like:

      **Speaker Name**: sentence one. sentence two. ...

    Groups appear in the same order as in the JSON.
    """
    groups = _load_groups_from_json(input_path)

    lines: List[str] = []

    for group in groups:
        if not isinstance(group, Mapping):
            continue

        speaker_raw = group.get("speaker", "")
        speaker = str(speaker_raw).strip()

        raw_segments = group.get("segments") or []
        if not isinstance(raw_segments, list):
            raise ValueError("Each group 'segments' field must be a list.")

        text = _concat_group_segments(raw_segments)

        # If there's nothing to say for this group, skip it.
        if not text and not speaker:
            continue

        if speaker:
            if text:
                # NOTE: colon after speaker, per your request
                lines.append(f"**{speaker}**: {text}")
            else:
                # Speaker but no text (weird but possible)
                lines.append(f"**{speaker}**:")
        else:
            # No speaker; just output the text.
            lines.append(text)

        # Blank line between groups for readability.
        lines.append("")

    markdown = "\n".join(lines).rstrip() + "\n"

    with output_path.open("w", encoding="utf-8") as f:
        f.write(markdown)
