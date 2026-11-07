"""Bounded, deterministic interleaving of rights-cleared source clips.

Unlike grouping each source's shots together, alternating independent original
recordings can create visibly more varied edits. Only SOURCE assignment is
planned here: exact intra-source timecodes are chosen later from real footage
by the existing technically scored editor.
"""
from __future__ import annotations

from dataclasses import dataclass

MAX_BEAM = 128
MAX_SCENES = 150
MAX_SOURCES = 32


@dataclass(frozen=True)
class _State:
    used_ms: tuple[int, ...]
    order: tuple[int, ...]
    last: int
    changes: int
    used_mask: int

    def rank(self, capacities: tuple[int, ...]) -> tuple:
        # Maximize source transitions first, then number of distinct source
        # recordings, and lastly spread the load over the available originals.
        load = max(
            (used / cap for used, cap in zip(self.used_ms, capacities) if cap),
            default=0.0,
        )
        return (
            self.changes,
            self.used_mask.bit_count(),
            -round(load, 6),
            # Deterministic ties prefer earlier source index, not randomness.
            tuple(-index for index in self.order),
        )


def interleave_sources(
    scene_ms: list[int], capacities_ms: list[int], *, beam_width: int = MAX_BEAM,
) -> tuple[int, ...]:
    """Choose per-scene source indices, never repeating source timeline bytes.

    Source clips remain in the caller's approved list and cannot exceed
    their measured durations. For each source, the timeline cursor remains
    increasing when excerpts are extracted by the editor. This is a bounded
    optimization, not an exhaustive global optimum or semantic match.
    """
    if (not 1 <= len(scene_ms) <= MAX_SCENES
            or not 1 <= len(capacities_ms) <= MAX_SOURCES
            or type(beam_width) is not int or not 1 <= beam_width <= MAX_BEAM
            or any(type(x) is not int or x < 500 for x in scene_ms)
            or any(type(x) is not int or x < 0 for x in capacities_ms)):
        raise ValueError("Invalid bounded scene/source schedule")
    if sum(scene_ms) > sum(capacities_ms):
        raise ValueError("Insufficient original source footage for all scenes")
    capacities = tuple(capacities_ms)
    beam = [_State((0,) * len(capacities), (), -1, 0, 0)]
    total = sum(scene_ms)
    used = 0
    for duration in scene_ms:
        used += duration
        possible: dict[tuple[tuple[int, ...], int], _State] = {}
        for previous in beam:
            for index, available in enumerate(capacities):
                if previous.used_ms[index] + duration > available:
                    continue
                utilization = list(previous.used_ms)
                utilization[index] += duration
                next_used = tuple(utilization)
                if sum(capacities) - sum(next_used) < total - used:
                    continue
                state = _State(
                    next_used, previous.order + (index,), index,
                    previous.changes + int(previous.last >= 0 and previous.last != index),
                    previous.used_mask | (1 << index),
                )
                key = (next_used, index)
                prior = possible.get(key)
                if prior is None or state.rank(capacities) > prior.rank(capacities):
                    possible[key] = state
        if not possible:
            raise ValueError("No feasible bounded source interleaving for all scenes")
        beam = sorted(
            possible.values(), key=lambda s: s.rank(capacities), reverse=True,
        )[:beam_width]
    chosen = max(beam, key=lambda s: s.rank(capacities))
    return chosen.order


def counts_for_schedule(schedule: tuple[int, ...], source_count: int) -> tuple[int, ...]:
    if (not schedule or type(source_count) is not int or
            not 1 <= source_count <= MAX_SOURCES or
            any(type(x) is not int or not 0 <= x < source_count for x in schedule)):
        raise ValueError("Invalid source schedule")
    return tuple(schedule.count(i) for i in range(source_count))
