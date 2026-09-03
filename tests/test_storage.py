"""Unit tests for ConversationStorage."""
from __future__ import annotations

import threading

from conversation_storage import ConversationStorage


def test_save_and_get_roundtrip(tmp_path):
    storage = ConversationStorage(str(tmp_path / "conv.db"))
    items = [{"role": "user", "content": "hello"}, {"role": "assistant", "content": "hi"}]
    assert storage.save_conversation("c1", items) is True
    got = storage.get_conversation("c1")
    assert got == items
    storage.close()


def test_get_missing_returns_none(tmp_path):
    storage = ConversationStorage(str(tmp_path / "conv.db"))
    assert storage.get_conversation("nope") is None
    storage.close()


def test_delete(tmp_path):
    storage = ConversationStorage(str(tmp_path / "conv.db"))
    storage.save_conversation("c2", [{"role": "user", "content": "x"}])
    assert storage.delete_conversation("c2") is True
    assert storage.delete_conversation("c2") is False
    storage.close()


def test_list_conversations(tmp_path):
    storage = ConversationStorage(str(tmp_path / "conv.db"))
    storage.save_conversation("a", [{"role": "user", "content": "1"}])
    storage.save_conversation("b", [{"role": "user", "content": "2"}])
    ids = set(storage.list_conversations())
    assert ids == {"a", "b"}
    storage.close()


def test_overwrite_existing(tmp_path):
    storage = ConversationStorage(str(tmp_path / "conv.db"))
    storage.save_conversation("c3", [{"role": "user", "content": "v1"}])
    storage.save_conversation("c3", [{"role": "user", "content": "v2"}])
    got = storage.get_conversation("c3")
    assert got == [{"role": "user", "content": "v2"}]
    storage.close()


def test_concurrent_writes(tmp_path):
    """Thread-safe: many threads writing distinct ids must all succeed."""
    storage = ConversationStorage(str(tmp_path / "conv.db"))
    n = 20

    def writer(i):
        storage.save_conversation(f"k{i}", [{"content": str(i)}])

    threads = [threading.Thread(target=writer, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    ids = set(storage.list_conversations())
    assert ids == {f"k{i}" for i in range(n)}
    storage.close()
