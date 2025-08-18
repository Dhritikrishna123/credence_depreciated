from __future__ import annotations

import os
import sys
import time
import subprocess
import socket


def wait_for(host: str, port: int, timeout: int = 90) -> None:
	"""Wait until a TCP host:port is connectable or timeout.

	Args:
		host: Hostname to connect to
		port: Port to connect to
		timeout: Seconds to wait before failing
	"""
	deadline = time.time() + timeout
	while time.time() < deadline:
		try:
			with socket.create_connection((host, port), timeout=2):
				return
		except OSError:
			time.sleep(1)
	raise RuntimeError(f"Timeout waiting for {host}:{port}")


def run(cmd: list[str]) -> int:
	return subprocess.call(cmd)


def main() -> int:
	mode = sys.argv[1] if len(sys.argv) > 1 else "api"

	# Parse DB host/port from URL like postgresql+psycopg://user:pass@host:port/db
	pg_url = os.environ.get(
		"CREDENCE_DATABASE_URL",
		"postgresql+psycopg://credence:credence@postgres:5432/credence",
	)
	pg_host = "postgres"
	pg_port = 5432
	try:
		if "@" in pg_url:
			after_at = pg_url.split("@", 1)[1]
			host_port = after_at.split("/", 1)[0]
			if ":" in host_port:
				pg_host, pg_port_str = host_port.split(":", 1)
				pg_port = int(pg_port_str)
			else:
				pg_host = host_port
	except Exception:
		pass

	# Wait for Postgres and Redis
	wait_for(pg_host, pg_port, timeout=120)
	wait_for("redis", 6379, timeout=60)

	# Run migrations only in API to avoid concurrency on version table
	if mode == "api":
		print("[entrypoint] Running Alembic migrations...", flush=True)
		ret = run(["alembic", "upgrade", "head"])
		if ret != 0:
			print("[entrypoint] Alembic failed", file=sys.stderr)
			return ret

	if mode == "api":
		return run(["uvicorn", "credence.api.main:app", "--host", "0.0.0.0", "--port", "8000"])
	if mode == "worker":
		return run(["celery", "-A", "credence.worker:celery_app", "worker", "--loglevel=info"])

	print(f"[entrypoint] Unknown mode: {mode}", file=sys.stderr)
	return 2


if __name__ == "__main__":
	os._exit(main())


