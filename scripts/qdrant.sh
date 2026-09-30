#!/usr/bin/env bash
# Manage local Qdrant for species retrieval (mirrors scripts/opik.sh ergonomics).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_DIR="$ROOT/docker/qdrant"
COMPOSE_FILE="$COMPOSE_DIR/docker-compose.yml"

resolve_docker() {
  if command -v docker >/dev/null 2>&1; then
    DOCKER=(docker)
    return 0
  fi
  for candidate in /usr/local/opt/docker/bin/docker /opt/homebrew/opt/docker/bin/docker; do
    if [[ -x "$candidate" ]]; then
      DOCKER=("$candidate")
      return 0
    fi
  done
  return 1
}

require_docker() {
  if ! resolve_docker; then
    echo "docker CLI not found on PATH." >&2
    exit 1
  fi
  if ! "${DOCKER[@]}" info >/dev/null 2>&1; then
    echo "Docker daemon is not reachable. Start Colima or Docker Desktop, then retry." >&2
    exit 1
  fi
}

compose() {
  require_docker
  "${DOCKER[@]}" compose -f "$COMPOSE_FILE" "$@"
}

usage() {
  cat <<EOF
Usage: $(basename "$0") <command>

Commands:
  up       Start Qdrant in the background
  down     Stop Qdrant (pass -v to remove volumes)
  status   Show compose service status
  health   Wait until Qdrant HTTP port responds
  seed     Upsert built retrieval index (requires manifest under artifacts/retrieval_index)
  logs     Follow Qdrant logs
EOF
}

wait_for_health() {
  local attempts=30
  local delay=2
  for ((i = 1; i <= attempts; i++)); do
    if curl -sf "http://127.0.0.1:6333/readyz" >/dev/null 2>&1; then
      echo "Qdrant is healthy."
      return 0
    fi
    sleep "$delay"
  done
  echo "Qdrant did not become healthy in time." >&2
  return 1
}

case "${1:-}" in
  up)
    compose up -d "${@:2}"
    echo
    echo "Qdrant HTTP: http://127.0.0.1:6333"
    wait_for_health || true
    ;;
  down)
    compose down "${@:2}"
    ;;
  status)
    compose ps "${@:2}"
    ;;
  health)
    wait_for_health
    ;;
  seed)
    export PATH="${HOME}/.local/bin:${PATH}"
    (cd "$ROOT" && uv run python -m eval.seed_retrieval_index "${@:2}")
    ;;
  logs)
    shift
    compose logs -f "$@"
    ;;
  *)
    usage
    exit 1
    ;;
esac
