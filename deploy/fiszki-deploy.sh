#!/usr/bin/env bash
# Auto-deploy fiszek na VPS (model "pull"): wdraża najnowszy GitHub Release.
# Uruchamiany co 5 min przez fiszki-deploy.timer. GitHub nie ma dostępu do serwera.
#
# Release powstaje tylko po zielonym CI (release.yml), więc wdrażamy tylko sprawdzone tagi.
# Pliki serwera spoza repo (.env, Caddyfile, docker-compose.override.yml) nie są ruszane.
set -euo pipefail

REPO_DIR="${REPO_DIR:-/opt/fiszki-hiszpanski}"
RELEASE_API="${RELEASE_API:-https://api.github.com/repos/SyBeer/HN_Fiszki/releases/latest}"
GIT_REMOTE="${GIT_REMOTE:-origin}"
COMPOSE="${COMPOSE:-docker compose}"
HEALTH_CMD="${HEALTH_CMD:-curl -fsS -o /dev/null http://127.0.0.1:8085/}"
HEALTH_TRIES="${HEALTH_TRIES:-30}"
HEALTH_SLEEP="${HEALTH_SLEEP:-2}"
LOCK_FILE="${LOCK_FILE:-/run/fiszki-deploy.lock}"

log() { echo "fiszki-deploy: $*"; }

# jeden przebieg naraz
if command -v flock >/dev/null 2>&1; then
  exec 9>"$LOCK_FILE"
  flock -n 9 || { log "inny przebieg trwa - pomijam"; exit 0; }
fi

cd "$REPO_DIR"

# 1. najnowszy Release z GitHuba (publiczne API, bez tokenu)
if ! json="$(curl -fsSL --max-time 20 -H 'Accept: application/vnd.github+json' "$RELEASE_API" 2>/dev/null)"; then
  log "brak Release albo brak połączenia z GitHubem - nic do zrobienia"
  exit 0
fi
tag="$(printf '%s\n' "$json" | sed -n 's/^[[:space:]]*"tag_name":[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)"

if [[ ! "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  log "nieprawidłowa nazwa tagu Release: '$tag' - przerywam"
  exit 1
fi

current="$(git describe --tags --exact-match HEAD 2>/dev/null || echo brak)"
if [[ "$current" == "$tag" ]]; then
  log "wersja $tag jest aktualna"
  exit 0
fi

# 2. ręczne zmiany w plikach z repo blokują wdrożenie (nie nadpisujemy ich po cichu)
if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  log "pliki z repo zmienione ręcznie na serwerze - przerywam (sprawdź: git status)"
  exit 1
fi

git fetch -q --tags --force "$GIT_REMOTE"
if ! git rev-parse -q --verify "refs/tags/$tag^{commit}" >/dev/null; then
  log "tagu $tag nie ma w repo $GIT_REMOTE - przerywam"
  exit 1
fi

previous="$(git rev-parse HEAD)"

healthy() {
  local i
  for ((i = 1; i <= HEALTH_TRIES; i++)); do
    if bash -c "$HEALTH_CMD" >/dev/null 2>&1; then return 0; fi
    sleep "$HEALTH_SLEEP"
  done
  return 1
}

# 3. wdrożenie
log "wdrażam $tag (było: $current)"
git checkout -q --detach "refs/tags/$tag"
if $COMPOSE up -d --build && healthy; then
  log "wdrożono $tag"
  exit 0
fi

# 4. rollback
log "$tag nie przeszedł testu zdrowia - wracam do $current"
git checkout -q --detach "$previous"
$COMPOSE up -d --build || true
exit 1
