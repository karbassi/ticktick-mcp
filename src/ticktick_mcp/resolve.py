from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from Levenshtein import distance as levenshtein_distance


def resolve_name(
    query: str,
    items: Sequence[Any],
    get_name: Callable[[Any], str],
    get_id: Callable[[Any], str],
    entity_type: str = "item",
) -> str:
    """Resolve a user-provided name or ID to an actual ID.

    Resolution order:
    1. If query looks like a hex ID (>=20 hex chars), return as-is
    2. Exact name match (case-insensitive)
    3. Single substring match
    4. Levenshtein suggestion (threshold <= 3)
    5. Ambiguous multiple matches error

    Returns the resolved ID string.
    """
    # 1. Hex ID passthrough
    if len(query) >= 20 and all(c in "0123456789abcdefABCDEF" for c in query):
        return query

    search = query.lower()

    # 2. Exact match (case-insensitive)
    for item in items:
        if get_name(item).lower() == search:
            return get_id(item)

    # 3. Contains match
    matches = [item for item in items if search in get_name(item).lower()]

    if len(matches) == 1:
        return get_id(matches[0])

    if len(matches) > 1:
        names = [get_name(m) for m in matches]
        raise ValueError(
            f"Multiple {entity_type}s match '{query}': {', '.join(names)}. "
            f"Use a more specific name or the full ID."
        )

    # 4. No match — try Levenshtein suggestion
    msg = f"No {entity_type} found matching '{query}'"
    if items:
        closest_name = ""
        closest_dist = 999
        for item in items:
            dist = levenshtein_distance(search, get_name(item).lower())
            if dist < closest_dist:
                closest_dist = dist
                closest_name = get_name(item)
        if closest_dist <= 3:
            msg += f". Did you mean '{closest_name}'?"

    raise ValueError(msg)


def resolve_name_with_etag(
    query: str,
    items: Sequence[Any],
    get_name: Callable[[Any], str],
    get_id: Callable[[Any], str],
    get_etag: Callable[[Any], str],
    entity_type: str = "item",
) -> tuple[str, str]:
    """Like resolve_name but also returns the etag.

    Returns (id, etag).
    """
    # Hex ID passthrough — find the item to get etag
    if len(query) >= 20 and all(c in "0123456789abcdefABCDEF" for c in query):
        for item in items:
            if get_id(item) == query:
                return get_id(item), get_etag(item)
        return query, ""

    search = query.lower()

    # Exact match
    for item in items:
        if get_name(item).lower() == search:
            return get_id(item), get_etag(item)

    # Contains match
    matches = [item for item in items if search in get_name(item).lower()]

    if len(matches) == 1:
        return get_id(matches[0]), get_etag(matches[0])

    if len(matches) > 1:
        names = [get_name(m) for m in matches]
        raise ValueError(
            f"Multiple {entity_type}s match '{query}': {', '.join(names)}. "
            f"Use a more specific name or the full ID."
        )

    msg = f"No {entity_type} found matching '{query}'"
    if items:
        closest_name = ""
        closest_dist = 999
        for item in items:
            dist = levenshtein_distance(search, get_name(item).lower())
            if dist < closest_dist:
                closest_dist = dist
                closest_name = get_name(item)
        if closest_dist <= 3:
            msg += f". Did you mean '{closest_name}'?"

    raise ValueError(msg)
