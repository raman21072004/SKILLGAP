"""Apply the data-retention policy now (also runs automatically at backend start-up).

    python scripts/purge_expired.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database.session import SessionLocal  # noqa: E402
from app.services.user_service import purge_expired  # noqa: E402

if __name__ == "__main__":
    with SessionLocal() as db:
        print(f"Deleted {purge_expired(db)} expired analyses.")
