"""File-based long-term memory store.

Persists key/value notes and arbitrary markdown documents under a directory.
The agent reads and writes via the MCP tools defined in `tools/memory_tools.py`.
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path


def _default_dir() -> Path:
    return Path(os.environ.get("SUPER_AGENT_MEMORY_DIR", "./memory_store")).resolve()


class MemoryStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or _default_dir()
        self.root.mkdir(parents=True, exist_ok=True)
        self.kv_path = self.root / "kv.json"
        self.notes_dir = self.root / "notes"
        self.notes_dir.mkdir(exist_ok=True)

    def _load_kv(self) -> dict:
        if not self.kv_path.exists():
            return {}
        try:
            return json.loads(self.kv_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

    def _save_kv(self, data: dict) -> None:
        self.kv_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def remember(self, key: str, value: str) -> None:
        data = self._load_kv()
        data[key] = {
            "value": value,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self._save_kv(data)

    def recall(self, key: str) -> str | None:
        entry = self._load_kv().get(key)
        return entry["value"] if entry else None

    def list_keys(self) -> list[str]:
        return sorted(self._load_kv().keys())

    def forget(self, key: str) -> bool:
        data = self._load_kv()
        if key in data:
            del data[key]
            self._save_kv(data)
            return True
        return False

    def _safe_filename(self, title: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9_\-]+", "-", title.strip()).strip("-").lower()
        return (slug or "note")[:80] + ".md"

    def save_note(self, title: str, content: str) -> str:
        fname = self._safe_filename(title)
        path = self.notes_dir / fname
        header = f"# {title}\n\n_Saved: {datetime.now(timezone.utc).isoformat()}_\n\n"
        path.write_text(header + content, encoding="utf-8")
        return str(path.relative_to(self.root))

    def list_notes(self) -> list[str]:
        return sorted(p.name for p in self.notes_dir.glob("*.md"))

    def read_note(self, filename: str) -> str | None:
        # Prevent path traversal.
        safe = Path(filename).name
        path = self.notes_dir / safe
        if not path.exists() or not path.is_file():
            return None
        return path.read_text(encoding="utf-8")

    def search_notes(self, query: str, limit: int = 5) -> list[tuple[str, str]]:
        """Return (filename, snippet) pairs that contain `query` (case-insensitive)."""
        q = query.lower()
        results: list[tuple[str, str]] = []
        for path in self.notes_dir.glob("*.md"):
            text = path.read_text(encoding="utf-8")
            if q in text.lower():
                idx = text.lower().find(q)
                start = max(0, idx - 80)
                end = min(len(text), idx + len(query) + 120)
                snippet = text[start:end].replace("\n", " ")
                results.append((path.name, snippet))
                if len(results) >= limit:
                    break
        return results
