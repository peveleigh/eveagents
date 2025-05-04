"""Logic to save conversations to a database."""

from __future__ import annotations

import json
import sqlite3


class ConversationStorage:
    """A class to handle storing and retrieving conversation data using SQLite."""

    def __init__(self, db_path: str = "conversations.db") -> None:
        """Initialize the ConversationStorage with a path to the SQLite database.

        Args:
            db_path: Path to the SQLite database file

        """
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self) -> None:
        """Create the conversations table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create table if it doesn't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id TEXT PRIMARY KEY,
            input_items TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        conn.commit()
        conn.close()

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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Convert input_items to JSON string for storage
            input_items_json = json.dumps(input_items)

            # Use INSERT OR REPLACE to handle both new and existing conversations
            # This will insert a new row if conversation_id doesn't exist,
            # or replace the existing row if it does
            cursor.execute(
                """
                INSERT OR REPLACE INTO conversations (conversation_id, input_items, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                """,
                (conversation_id, input_items_json),
            )

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error saving conversation: {e}")
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "SELECT input_items FROM conversations WHERE conversation_id = ?",
                (conversation_id,),
            )

            result = cursor.fetchone()
            conn.close()

            if result:
                # Convert JSON string back to list of dictionaries
                return json.loads(result[0])
        except Exception as e:
            print(f"Error retrieving conversation: {e}")
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
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM conversations WHERE conversation_id = ?", 
                (conversation_id,)
            )

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            return False

        return cursor.rowcount > 0


    def list_conversations(self) -> list[str]:
        """List all conversation IDs in the database.

        Returns:
            List of conversation IDs

        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT conversation_id FROM conversations")

            result = cursor.fetchall()
            conn.close()

            return [row[0] for row in result]

        except Exception as e:
            print(f"Error listing conversations: {e}")
            return []



