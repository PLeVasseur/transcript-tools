from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping


def group_consecutive_segments(
    segments: Iterable[Mapping[str, Any]],
) -> Dict[str, Any]:
    """
    Given slimmed segments of the form:
      {"text": "...", "speaker": "SPEAKER_01"}
    return grouped segments of the form:
      {
        "segments": [
          {
            "speaker": "SPEAKER_01",
            "segments": ["utterance 1", "utterance 2"]
          },
          {
            "speaker": "SPEAKER_00",
            "segments": ["utterance 3"]
          }
        ]
      }

    Grouping happens only for *consecutive* segments with the same speaker.
    """
    grouped: list[Dict[str, Any]] = []

    current_speaker: Any = None
    current_utts: list[str] = []

    for seg in segments:
        speaker = seg.get("speaker")
        text = seg.get("text", "")

        if speaker != current_speaker:
            # Flush previous group
            if current_speaker is not None:
                grouped.append(
                    {
                        "speaker": current_speaker,
                        "segments": current_utts,
                    }
                )
            current_speaker = speaker
            current_utts = [text]
        else:
            current_utts.append(text)

    # Flush last group
    if current_speaker is not None:
        grouped.append(
            {
                "speaker": current_speaker,
                "segments": current_utts,
            }
        )

    return {"segments": grouped}


def group_consecutive_segments_file(
    input_path: str | Path,
    output_path: str | Path,
) -> None:
    """
    Read a 'slimmed' JSON (with top-level 'segments' list of {text, speaker}),
    group consecutive segments by speaker, and write the grouped JSON.
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

    grouped = group_consecutive_segments(segments)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(grouped, f, ensure_ascii=False, indent=2)
