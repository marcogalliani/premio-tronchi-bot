from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class RankingRow:
    player_name: str
    score: int


class Storage:
    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._ensure_tables()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_tables(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ranking (
                    player_name TEXT PRIMARY KEY,
                    score INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_sources (
                    source_id TEXT PRIMARY KEY,
                    processed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def is_source_processed(self, source_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM processed_sources WHERE source_id = ?",
                (source_id,),
            ).fetchone()
        return row is not None

    def mark_source_processed(self, source_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO processed_sources(source_id) VALUES (?)",
                (source_id,),
            )

    def apply_penalties(self, players: Iterable[str], source_id: str) -> int:
        unique_players = {name.strip() for name in players if name and name.strip()}
        with self._connect() as conn:
            for player in unique_players:
                conn.execute(
                    """
                    INSERT INTO ranking(player_name, score)
                    VALUES (?, 1)
                    ON CONFLICT(player_name)
                    DO UPDATE SET score = score + 1
                    """,
                    (player,),
                )
            conn.execute(
                "INSERT OR IGNORE INTO processed_sources(source_id) VALUES (?)",
                (source_id,),
            )
        return len(unique_players)

    def get_ranking(self, limit: int = 20) -> list[RankingRow]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT player_name, score
                FROM ranking
                ORDER BY score DESC, player_name ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [RankingRow(player_name=row["player_name"], score=row["score"]) for row in rows]

