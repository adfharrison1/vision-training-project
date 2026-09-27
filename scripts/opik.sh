#!/usr/bin/env bash
# Manage the optional local Opik stack (self-hosted observability).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_DIR="$ROOT/docker/opik"
UPSTREAM="$COMPOSE_DIR/.upstream"
ENV_FILE="$COMPOSE_DIR/.env"
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
    cat <<EOF >&2
docker CLI not found on PATH.

Install via Homebrew:
  brew install docker docker-compose colima
  brew link docker

Then start a local runtime:
  colima start
EOF
    exit 1
  fi

  if ! "${DOCKER[@]}" info >/dev/null 2>&1; then
    cat <<EOF >&2
Docker daemon is not reachable.

If you use Colima (detected on this machine):
  colima start
  colima status

Then retry:
  ./scripts/opik.sh up
EOF
    exit 1
  fi
}

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE" >&2
  exit 1
fi

OPIK_TAG="$(grep -E '^OPIK_VERSION=' "$ENV_FILE" | cut -d= -f2- | tr -d '\r')"
if [[ -z "$OPIK_TAG" ]]; then
  echo "OPIK_VERSION is not set in $ENV_FILE" >&2
  exit 1
fi

ensure_upstream() {
  if [[ -f "$UPSTREAM/deployment/docker-compose/docker-compose.yaml" ]]; then
    return 0
  fi
  echo "Fetching Opik ${OPIK_TAG} deployment files into docker/opik/.upstream ..."
  rm -rf "$UPSTREAM"
  git clone --depth 1 --branch "${OPIK_TAG}" https://github.com/comet-ml/opik.git "$UPSTREAM"
}

compose() {
  require_docker
  ensure_upstream
  "${DOCKER[@]}" compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" --profile opik "$@"
}

usage() {
  cat <<EOF
Usage: $(basename "$0") <command>

Commands:
  up       Start Opik (docker compose --profile opik up -d)
  down     Stop Opik containers
  status   Show container status
  logs     Follow Opik logs (pass service names to filter)
  pull     Pull pinned Opik images

UI:  http://localhost:5173
API: http://127.0.0.1:5173/api

Enable tracing in plant-id:
  export PLANT_ID_OPIK_ENABLED=true
EOF
}

case "${1:-}" in
  up)
    compose up -d --pull never "${@:2}"
    echo
    echo "Opik UI:  http://localhost:5173"
    echo "Opik API: http://127.0.0.1:5173/api"
    echo "First start may take a few minutes while services become healthy."
    ;;
  down)
    compose down "${@:2}"
    ;;
  status)
    compose ps "${@:2}"
    ;;
  logs)
    shift
    compose logs -f "$@"
    ;;
  pull)
    compose pull "${@:2}"
    ;;
  *)
    usage
    exit 1
    ;;
esac
