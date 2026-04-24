#!/usr/bin/env python3
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml


repo_root = Path(__file__).parent.parent
config_path = repo_root / "config.yaml"
generated_dir = repo_root / ".docker"
generated_env_path = generated_dir / "compose.env"


def require_config() -> dict:
    if not config_path.exists():
        raise SystemExit("config.yaml not found. Copy config.yaml.example to config.yaml first.")
    with config_path.open("r", encoding="utf-8") as config_file:
        config = yaml.safe_load(config_file) or {}
    if not isinstance(config, dict):
        raise SystemExit("config.yaml must be a YAML mapping.")
    return config


def write_compose_env(config: dict) -> None:
    database_url = (config.get("database") or {}).get("url")
    if not database_url:
        raise SystemExit("database.url is required in config.yaml")

    parsed = urlparse(database_url)
    if parsed.hostname != "postgres":
        raise SystemExit(
            "For Docker Compose, set database.url to "
            "postgresql://paper:<password>@postgres:5432/paper_online in config.yaml"
        )
    db_name = parsed.path.lstrip("/") or "paper_online"
    db_user = parsed.username or "paper"
    db_password = parsed.password or "paper"
    server_port = str((config.get("server") or {}).get("port") or 8000)
    docker_config = config.get("docker") or {}
    postgres_port = str(docker_config.get("postgres_port") or 5432)

    generated_dir.mkdir(exist_ok=True)
    generated_env_path.write_text(
        "\n".join(
            [
                f"POSTGRES_DB={db_name}",
                f"POSTGRES_USER={db_user}",
                f"POSTGRES_PASSWORD={db_password}",
                f"POSTGRES_PORT={postgres_port}",
                f"PORT={server_port}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> int:
    config = require_config()
    write_compose_env(config)
    args = sys.argv[1:] or ["up", "--build", "-d"]
    return subprocess.run(
        ["docker", "compose", "--env-file", str(generated_env_path), *args],
        cwd=repo_root,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
