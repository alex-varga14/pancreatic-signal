#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTDIR="$(dirname "$ROOT")"

cd "$OUTDIR"
ZIP_NAME="pancreatic-signal-scaffold.zip"
TAR_NAME="pancreatic-signal-scaffold.tar.gz"

rm -f "$ZIP_NAME" "$TAR_NAME"
zip -qr "$ZIP_NAME" pancreatic-signal
tar -czf "$TAR_NAME" pancreatic-signal

echo "Created:"
echo " - $OUTDIR/$ZIP_NAME"
echo " - $OUTDIR/$TAR_NAME"
