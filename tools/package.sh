#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="${1:-$ROOT/build}"
"$ROOT/tools/build.sh" "$BUILD"

VERSION="$("$BUILD/open-spin-fv1" --version | awk '{print $2}')"
OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"
NAME="open-spin-fv1-${VERSION}-${OS}-${ARCH}"
DIST="$ROOT/dist"
STAGE="$DIST/$NAME"
rm -rf "$STAGE"
mkdir -p "$STAGE/bin"
cp "$BUILD/open-spin-fv1" "$STAGE/bin/"
cp "$ROOT/LICENSE" "$STAGE/"
cp "$ROOT/README.md" "$STAGE/"
(
  cd "$DIST"
  tar -czf "$NAME.tar.gz" "$NAME"
)
sha256sum "$DIST/$NAME.tar.gz" > "$DIST/$NAME.tar.gz.sha256"
echo "$DIST/$NAME.tar.gz"
