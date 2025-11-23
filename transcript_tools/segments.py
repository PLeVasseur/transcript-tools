from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, MutableMapping, Optional


SpeakerMap = Mapping[str, str]


def _normalize_speaker_map(raw: Any) -> SpeakerMap:
    """
    Normalize a user-provided 'array of mappings' or dict into
    a simple { "SPEAKER_XX": "Name" } mapping.

    Accepted formats:

    1) Direct dict:
       {
         "SPEAKER_00": "Alice Jones",
         "SPEAKER_01": "Bob Smith"
       }

    2) List of one-key dicts:
       [
         {"SPEAKER_00": "Alice Jones"},
         {"SPEAKER_01": "Bob Smith"}
       ]

    3) List of {"from": ..., "to": ...} dicts:
       [
         {"from": "SPEAKER_00", "to": "Alice Jones"}
         {"from": "SPEAKER_01", "to": "Bob Smith"},
       ]
    """
    if raw is None:
        return {}

    # Case 1: direct mapping
    if isinstance(raw, Mapping):
        return {str(k): str(v) for k, v in raw.items()}

    # Case 2 & 3: list of dicts
    if isinstance(raw, Iterable) and not isinstance(raw, (str, bytes)):
        mapping: Dict[str, str] = {}
        for item in raw:
            if not isinstance(item, Mapping):
                raise ValueError(
                    "Invalid speaker map item; expected mapping objects inside list."
                )

            if "from" in item and "to" in item:
                src = str(item["from"])
                dst = str(item["to"])
                mapping[src] = dst
            else:
                if len(item) != 1:
                    raise ValueError(
                        "List-based speaker map dicts must be either "
                        "{'from': ..., 'to': ...} or single-key mappings."
                    )
                (src, dst), = item.items()
                mapping[str(src)] = str(dst)

        return mapping

    raise ValueError(
        "Speaker map must be a dict or a list of mapping objects; "
        f"got {type(raw)!r} instead."
    )


def transform_segments(
    segments: Iterable[Mapping[str, Any]],
    speaker_map: Optional[SpeakerMap] = None,
) -> Dict[str, Any]:
    """
    Transform a list of segments into a new structure where each segment only
    contains { 'text': ..., 'speaker': ... }.

    If 'speaker_map' is provided, any segment 'speaker' present in the map
    is replaced by the mapped name.
    """
    speaker_map = speaker_map or {}
    result_segments = []

    for seg in segments:
        text = seg.get("text", "")
        raw_speaker = seg.get("speaker")

        if raw_speaker is not None and raw_speaker in speaker_map:
            speaker = speaker_map[raw_speaker]
        else:
            speaker = raw_speaker

        result_segments.append(
            {
                "text": text,
                "speaker": speaker,
            }
        )

    return {"segments": result_segments}


def transform_segments_file(
    input_path: str | Path,
    output_path: str | Path,
    speaker_map_raw: Optional[Any] = None,
) -> None:
    """
    Convenience wrapper that reads the input JSON, transforms segments, and
    writes the output JSON.

    Parameters
    ----------
    input_path:
        Path to the input JSON file containing a top-level 'segments' list.
    output_path:
        Path where the transformed JSON will be written.
    speaker_map_raw:
        Optional raw mapping/array as described in `_normalize_speaker_map`.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    segments = data.get("segments")
    if not isinstance(segments, list):
        raise ValueError(
            f"Expected top-level key 'segments' containing a list; "
            f"got {type(segments)!r}"
        )

    speaker_map = _normalize_speaker_map(speaker_map_raw)
    transformed = transform_segments(segments, speaker_map=speaker_map)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(transformed, f, ensure_ascii=False, indent=2)
