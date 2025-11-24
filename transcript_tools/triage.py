from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List, Optional


@dataclass
class Group:
    speaker: str
    segments: List[str]


def load_groups(path: Path) -> List[Group]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    raw_segments = data.get("segments")
    if not isinstance(raw_segments, list):
        raise ValueError(
            f"Expected top-level key 'segments' containing a list; "
            f"got {type(raw_segments)!r}"
        )

    groups: List[Group] = []
    for item in raw_segments:
        if not isinstance(item, dict):
            continue
        speaker = str(item.get("speaker", "") or "")
        segs = item.get("segments") or []
        if not isinstance(segs, list):
            raise ValueError("Each group 'segments' field must be a list of strings.")
        groups.append(Group(speaker=speaker, segments=[str(s) for s in segs]))
    return groups


def dump_groups(path: Path, groups: List[Group]) -> None:
    """
    Write the updated groups back out. We drop groups with no segments, since
    they don't carry any information.
    """
    payload = {
        "segments": [
            {"speaker": g.speaker, "segments": g.segments}
            for g in groups
            if g.segments
        ]
    }
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _print_group(label: str, group: Optional[Group]) -> None:
    print(f"{label}:")
    if group is None:
        print("  <none>")
        return

    print(f"  speaker: {group.speaker!r}")
    print("  segments:")
    if not group.segments:
        print("    <no segments>")
        return

    for idx, seg in enumerate(group.segments):
        text = seg.replace("\n", " ").strip()
        if len(text) > 160:
            text = text[:157] + "..."
        print(f"    [{idx}] {text}")


def _print_group_window(groups: List[Group], group_idx: int) -> None:
    preceding = groups[group_idx - 1] if group_idx > 0 else None
    active = groups[group_idx]
    following = groups[group_idx + 1] if group_idx + 1 < len(groups) else None

    print()
    _print_group("preceding group", preceding)
    print()
    _print_group("active group", active)
    print()
    _print_group("following group", following)
    print()


def _print_context_with_active_segment(
    groups: List[Group],
    group_idx: int,
    segment_idx: int,
) -> None:
    active = groups[group_idx]

    _print_group_window(groups, group_idx)

    print("active segment:")
    if 0 <= segment_idx < len(active.segments):
        text = active.segments[segment_idx].replace("\n", " ").strip()
        print(f"  [{segment_idx}] {text}")
    else:
        print("  <none>")
    print()


def _prompt_group_decision() -> str:
    """
    Prompt the user for what to do with the current group:

    - y: modify group segmentation
    - n: skip this group, no changes
    - w: write remaining groups without further triage
    - q: quit without writing any output
    """
    while True:
        answer = input(
            "modify group segmentation? (y/n) "
            "write remaining without further changes? (w) "
            "quit? (q) "
        ).strip().lower()

        if answer in ("y", "n", "w", "q"):
            return answer

        print("Please enter one of: y, n, w, q.")


def _prompt_action() -> str:
    """
    Per-segment action inside a group:

    - p: move this segment to the preceding group
    - c: keep this segment in the active group and move to the next segment
    - a: keep this and all remaining segments in the active group (done with this group)
    - f: move this and all remaining segments to the following group
    - n: create a new group with a new speaker for this segment
    - d: delete this segment
    """
    while True:
        answer = input(
            "preceding group (p), active group for current (c), "
            "active group for all remaining (a), following group for all remaining (f), "
            "new group (n), delete segment (d): "
        ).strip().lower()

        if answer in (
            "p",
            "c",
            "a",
            "f",
            "n",
            "d",
            "preceding",
            "current",
            "active",
            "following",
            "new",
            "delete",
        ):
            # Normalize to first letter: p / c / a / f / n / d
            return answer[0]

        print("Please enter one of: p, c, a, f, n, d.")


def _prompt_speaker_name() -> str:
    while True:
        name = input("speaker name? ").strip()
        if name:
            return name
        print("Speaker name cannot be empty.")


def _triage_single_group(groups: List[Group], group_idx: int) -> int:
    """
    Interactively triage a single group, possibly moving segments to the
    preceding/following groups, creating new groups, deleting segments,
    or just accepting them as-is.

    Returns the index of the next group to examine.
    """
    next_group_idx = group_idx + 1
    segment_idx = 0

    while True:
        active = groups[group_idx]

        if segment_idx >= len(active.segments):
            # No more segments to look at in this group.
            break

        _print_context_with_active_segment(groups, group_idx, segment_idx)
        action = _prompt_action()

        # Move current segment to preceding group.
        if action == "p":
            if group_idx == 0:
                print("No preceding group exists; cannot assign to preceding group.")
                continue

            preceding = groups[group_idx - 1]
            seg_text = active.segments.pop(segment_idx)
            preceding.segments.append(seg_text)

            if not active.segments:
                print("Active group now has no remaining segments.")
                break

            # Do NOT advance segment_idx: the next segment slides into this index.
            continue

        # Keep this segment in the active group and move to the next segment.
        if action == "c":
            segment_idx += 1
            continue

        # Keep all remaining segments in the active group; go to next group.
        if action == "a":
            next_group_idx = group_idx + 1
            break

        # Move current + all remaining segments to following group.
        if action == "f":
            if group_idx + 1 >= len(groups):
                print("No following group exists; cannot assign to following group.")
                continue

            following = groups[group_idx + 1]
            remaining = active.segments[segment_idx:]
            if remaining:
                # Keep earlier segments in the current group.
                active.segments = active.segments[:segment_idx]
                # Insert remaining at the front of the following group to preserve order.
                following.segments = remaining + following.segments

            # Next, we start triaging the following group from its first segment.
            next_group_idx = group_idx + 1
            break

        # Create a brand new group for this segment.
        if action == "n":
            new_name = _prompt_speaker_name()
            segs = active.segments

            before = segs[:segment_idx]
            current_seg = segs[segment_idx]
            after = segs[segment_idx + 1 :]

            new_groups_for_current: list[Group] = []
            if before:
                new_groups_for_current.append(
                    Group(speaker=active.speaker, segments=before)
                )

            new_groups_for_current.append(
                Group(speaker=new_name, segments=[current_seg])
            )

            if after:
                new_groups_for_current.append(
                    Group(speaker=active.speaker, segments=after)
                )

            # Replace the current group with up to three groups (before/new/after).
            groups[group_idx : group_idx + 1] = new_groups_for_current

            # New group's index is group_idx + (1 if there is a 'before' group).
            has_before = bool(before)
            group_idx = group_idx + (1 if has_before else 0)
            segment_idx = 0  # new group currently has only one segment

            # Continue triaging, now positioned on the new group.
            continue

        # Delete this segment.
        if action == "d":
            deleted = active.segments.pop(segment_idx)
            print(f"Deleted segment: {deleted!r}")

            if not active.segments:
                print("Active group now has no remaining segments.")
                break

            # Do not advance segment_idx; the next segment, if any,
            # is now at the same index.
            continue

    return next_group_idx


def run_triage(groups: List[Group], start_group: int = 1) -> bool:
    """
    Main triage loop. Walks through groups and gives you the chance to
    adjust segmentation on each one.

    Parameters
    ----------
    groups:
        List of Group objects to be triaged in-place.
    start_group:
        1-based index of the group at which to start triage. Defaults to 1
        (the first group).

    Returns
    -------
    bool
        True  -> caller should write out the groups (including any changes).
        False -> caller should NOT write (user chose to quit with 'q').
    """
    total = len(groups)
    if total == 0:
        print("No groups to triage.")
        return True

    if start_group < 1:
        start_group = 1

    if start_group > total:
        print(
            f"Requested start_group {start_group} but there are only {total} groups. "
            "Nothing to triage."
        )
        return True

    # Convert to 0-based index.
    group_idx = start_group - 1

    while group_idx < len(groups):
        print("\n" + "=" * 80)
        print(f"Group {group_idx + 1} of {len(groups)}")
        _print_group_window(groups, group_idx)

        decision = _prompt_group_decision()

        if decision == "n":
            # Skip this group; move on.
            group_idx += 1
            continue

        if decision == "y":
            # Enter per-segment triage for this group.
            group_idx = _triage_single_group(groups, group_idx)
            # After triage, loop continues from the returned group index.
            continue

        if decision == "w":
            # Write remaining without further changes:
            # just stop triaging and let the caller write out the current state.
            return True

        if decision == "q":
            # Quit without writing anything.
            return False

    # Finished triaging all groups; caller should write the result.
    return True
