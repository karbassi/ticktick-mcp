from __future__ import annotations

import pytest

from ticktick_mcp.resolve import resolve_name, resolve_name_with_etag


class Item:
    def __init__(self, id: str, name: str, etag: str = ""):
        self.id = id
        self.name = name
        self.etag = etag


ITEMS = [
    Item("id1", "Shopping"),
    Item("id2", "Work Tasks"),
    Item("id3", "Personal"),
]


class TestResolveName:
    def test_hex_id_passthrough(self):
        result = resolve_name(
            "abcdef1234567890abcdef",
            ITEMS,
            lambda i: i.name,
            lambda i: i.id,
        )
        assert result == "abcdef1234567890abcdef"

    def test_exact_match(self):
        result = resolve_name("Shopping", ITEMS, lambda i: i.name, lambda i: i.id)
        assert result == "id1"

    def test_exact_match_case_insensitive(self):
        result = resolve_name("shopping", ITEMS, lambda i: i.name, lambda i: i.id)
        assert result == "id1"

    def test_contains_match(self):
        result = resolve_name("Shop", ITEMS, lambda i: i.name, lambda i: i.id)
        assert result == "id1"

    def test_ambiguous_match(self):
        items = [Item("id1", "Test A"), Item("id2", "Test B")]
        with pytest.raises(ValueError, match="Multiple"):
            resolve_name("Test", items, lambda i: i.name, lambda i: i.id)

    def test_no_match_with_suggestion(self):
        with pytest.raises(ValueError, match="Did you mean"):
            resolve_name("Shoping", ITEMS, lambda i: i.name, lambda i: i.id)

    def test_no_match_no_suggestion(self):
        with pytest.raises(ValueError, match="No item found"):
            resolve_name("zzzzzzzzz", ITEMS, lambda i: i.name, lambda i: i.id)


class TestResolveNameWithEtag:
    def test_returns_etag(self):
        items = [Item("id1", "Test", "etag1")]
        id_, etag = resolve_name_with_etag(
            "Test",
            items,
            lambda i: i.name,
            lambda i: i.id,
            lambda i: i.etag,
        )
        assert id_ == "id1"
        assert etag == "etag1"

    def test_hex_id_with_etag(self):
        items = [Item("abcdef1234567890abcdef", "Test", "etag1")]
        id_, etag = resolve_name_with_etag(
            "abcdef1234567890abcdef",
            items,
            lambda i: i.name,
            lambda i: i.id,
            lambda i: i.etag,
        )
        assert id_ == "abcdef1234567890abcdef"
        assert etag == "etag1"
