#!/bin/bash
set -e

# Always work from the directory containing this script
cd "$(dirname "$0")"

# Determine persistent storage location
if [[ "$OS" == "Windows_NT" ]]; then
  PERSIST_DIR="${USERPROFILE//\\/\//}/Documents/vps-value-calculator"
else
  PERSIST_DIR="/opt/vps-value-calculator"
fi
export PERSIST_DIR
mkdir -p "$PERSIST_DIR/data" "$PERSIST_DIR/static/images"

# Fetch latest code and show changes
git fetch origin main
OLD=$(git rev-parse --short HEAD)
NEW=$(git rev-parse --short origin/main)
if [ "$OLD" != "$NEW" ]; then
  echo "Updating $OLD..$NEW"
  echo "Fast-forward"
  git --no-pager diff --stat HEAD origin/main
else
  echo "Already up to date."
fi

# Reset working tree to match remote
git reset --hard origin/main
git clean -fd

# Display the current commit for clarity
git log -1 --oneline

# Stop existing containers
docker compose down

# Remove dangling images
docker image prune -f

# Pull and rebuild images
docker compose pull
docker compose build --pull

# Start services in detached mode
docker compose up -d

# Optional: remove unused data
# docker system prune -f
