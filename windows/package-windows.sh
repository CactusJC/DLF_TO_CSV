#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
DIST_DIR="$BASE_DIR/dist/win-x86_64"
PACKAGE_DIR="$BASE_DIR/dist"
TIMESTAMP=$(date +"%Y%m%d-%H%M%S")
ARCHIVE_NAME="dlf_parser_helper_win-x86_64_$TIMESTAMP.zip"

# --- Main Script ---
echo "--- Packaging Windows build artifacts ---"

if [ ! -d "$DIST_DIR" ] || [ -z "$(ls -A "$DIST_DIR")" ]; then
    echo "Error: Build artifact directory '$DIST_DIR' is empty or does not exist."
    echo "Please run the build script (build-cross-ubuntu.sh) first."
    exit 1
fi

# Ensure the parent directory for the archive exists
mkdir -p "$PACKAGE_DIR"

# Create the archive
echo "Creating archive at '$PACKAGE_DIR/$ARCHIVE_NAME'..."
# The -j option ignores directory paths in the zip, storing files at the root.
# The 'cd' ensures the paths inside the zip are relative to the dist directory.
(cd "$DIST_DIR" && zip -r -j "$PACKAGE_DIR/$ARCHIVE_NAME" ./*)

echo "Packaging complete."
echo "Created artifact: $PACKAGE_DIR/$ARCHIVE_NAME"