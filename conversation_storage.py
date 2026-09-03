"""Logic to save conversations to a database."""

from __future__ import annotations

import json
import logging
import sqlite3
import threading

logger = logging.getLogger(__name__)


class ConversationStorage:
    """A class to handle storing and retrieving conversation data using SQLite.

    Uses a single shared connection opened with ``check_same_thread=False``
    guarded by a ``threading.Lock`` so it is safe to use across the async
    request handlers and gunicorn thread workers.

    """

    def __init__(self, db_path: str = "conversations.db") -> None:
        """Initialize the ConversationStorage with a path to the SQLite database.

        Args:
            db_path: Path to the SQLite database file

        """
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Create the conversations table if it doesn't exist."""
        with self._lock:
            cursor = self._conn.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                conversation_id TEXT PRIMARY KEY,
                input_items TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            self._conn.commit()

    def save_conversation(
        self,
        conversation_id: str,
        input_items: list[dict[str, str]],
    ) -> bool:
        """Save or update a conversation in the database.

        Args:
            conversation_id: Unique identifier for the conversation
            input_items: List of conversation items

        Returns:
            bool: True if successful, False otherwise

        """
        try:
            input_items_json = json.dumps(input_items)
            with self._lock:
                cursor = self._conn.cursor()
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO conversations (conversation_id, input_items, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                    """,
                    (conversation_id, input_items_json),
                )
                self._conn.commit()
        except sqlite3.Error:
            logger.exception("Error saving conversation %s", conversation_id)
            return False

        return True

    def get_conversation(self, conversation_id: str) -> list[dict[str, str]] | None:
        """Retrieve a conversation from the database by conversation_id.

        Args:
            conversation_id: Unique identifier for the conversation

        Returns:
            List of conversation items or None if not found

        """
        try:
            with self._lock:
                cursor = self._conn.cursor()
                cursor.execute(
                    "SELECT input_items FROM conversations WHERE conversation_id = ?",
                    (conversation_id,),
                )
                result = cursor.fetchone()

            if result:
                return json.loads(result[0])
        except sqlite3.Error:
            logger.exception("Error retrieving conversation %s", conversation_id)
            return None

        return None

    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation from the database.

        Args:
            conversation_id: Unique identifier for the conversation

        Returns:
            bool: True if successful, False otherwise

        """
        try:
            with self._lock:
                cursor = self._conn.cursor()
                cursor.execute(
                    "DELETE FROM conversations WHERE conversation_id = ?",
                    (conversation_id,),
                )
                self._conn.commit()
                rowcount = cursor.rowcount
        except sqlite3.Error:
            logger.exception("Error deleting conversation %s", conversation_id)
            return False

        return rowcount > 0

    def list_conversations(self) -> list[str]:
        """List all conversation IDs in the database.

        Returns:
            List of conversation IDs

        """
        try:
            with self._lock:
                cursor = self._conn.cursor()
                cursor.execute("SELECT conversation_id FROM conversations")
                result = cursor.fetchall()
        except sqlite3.Error:
            logger.exception("Error listing conversations")
            return []

        return [row[0] for row in result]

    def close(self) -> None:
        """Close the underlying database connection."""
        with self._lock:
            self._conn.close()
