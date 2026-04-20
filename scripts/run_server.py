#!/usr/bin/env python3
import sys
from pathlib import Path

import uvicorn

repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "backend"))

from config import settings


def main() -> None:
    uvicorn.run(
        "app:app",
        host=settings.server.host,
        port=settings.server.port,
    )


if __name__ == "__main__":
    main()
