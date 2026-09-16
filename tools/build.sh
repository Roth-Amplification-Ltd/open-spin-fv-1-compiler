#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD="${1:-$ROOT/build}"
GEN=()
if command -v ninja >/dev/null 2>&1; then GEN=(-G Ninja); fi
cmake -S "$ROOT" -B "$BUILD" "${GEN[@]}" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD" --parallel
ctest --test-dir "$BUILD" --output-on-failure
"$BUILD/open-spin-fv1" --version
