#!/usr/bin/env python3
import sys
from pathlib import Path

import yaml


repo_root = Path(__file__).parent.parent
config_path = repo_root / "config.yaml"


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: config_value.py dotted.path", file=sys.stderr)
        return 2
    if not config_path.exists():
        print("config.yaml not found", file=sys.stderr)
        return 1

    value: object = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    for part in sys.argv[1].split("."):
        if not isinstance(value, dict) or part not in value:
            print(f"{sys.argv[1]} not found", file=sys.stderr)
            return 1
        value = value[part]
    if value is None:
        return 1
    print(value)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
