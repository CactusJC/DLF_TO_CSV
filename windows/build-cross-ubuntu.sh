#!/usr/bin/env bash
set -euo pipefail

# --- Configuration ---
# Get the script's directory.
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
# Output directory for the final artifacts.
DIST_DIR="$BASE_DIR/dist/win-x86_64"
# Temporary directory for building dependencies.
BUILD_DIR=$(mktemp -d -p "/tmp" "libdivecomputer_build_XXXXXX")
# Libdivecomputer source code URL.
LIBDC_REPO="https://github.com/libdivecomputer/libdivecomputer.git"
# Staging directory for the cross-compiled libdivecomputer.
LIBDC_INSTALL_DIR="$BUILD_DIR/libdivecomputer_install"

# --- Helper Functions ---
log() {
  echo "--- $1 ---"
}

# --- Main Script ---
log "Starting the Windows cross-compile build process"

# 1. Clean previous artifacts
log "Cleaning previous build artifacts..."
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"
# Setup a trap to clean up the temporary build directory on exit.
trap 'log "Cleaning up temporary build directory..."; rm -rf "$BUILD_DIR"' EXIT

# 2. Install required packages (for Debian/Ubuntu)
log "Installing required system packages (requires sudo)..."
# In a non-interactive environment, frontend locks can cause issues.
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update
sudo apt-get install -y --no-install-recommends \
  git build-essential mingw-w64 pkg-config \
  autoconf automake libtool

# 3. Check for dependencies
log "Verifying build environment..."
"$BASE_DIR/check-deps.sh"

# 4. Clone and build libdivecomputer
log "Cloning libdivecomputer from $LIBDC_REPO..."
git clone --depth 1 "$LIBDC_REPO" "$BUILD_DIR/libdivecomputer"
cd "$BUILD_DIR/libdivecomputer"

log "Configuring libdivecomputer for Windows (x86_64)..."
autoreconf --install
./configure \
  --host=x86_64-w64-mingw32 \
  --build=$(./config.guess) \
  --prefix="$LIBDC_INSTALL_DIR" \
  --enable-shared \
  --disable-static

log "Building libdivecomputer..."
make -j$(nproc)
make install

# 5. Build dlf_parser_helper.exe
log "Building dlf_parser_helper.exe..."
cd "$BASE_DIR/../" # Go to project root
x86_64-w64-mingw32-gcc -Wall -O2 \
  -I"$LIBDC_INSTALL_DIR/include" \
  -L"$LIBDC_INSTALL_DIR/lib" \
  -o "$DIST_DIR/dlf_parser_helper.exe" \
  tools/dlf_parser_helper.c -ldivecomputer

log "Successfully built dlf_parser_helper.exe"

# 6. Collect required DLLs
log "Collecting required DLLs..."

# Copy libdivecomputer DLL using a wildcard to handle version numbers.
cp "$LIBDC_INSTALL_DIR/bin/libdivecomputer"*.dll "$DIST_DIR/"
log "Copied libdivecomputer DLL(s)."

# Use objdump to find other dependencies and copy them
log "Analyzing dlf_parser_helper.exe for other DLL dependencies..."

# Discover MinGW library paths dynamically from the compiler
GCC_LIB_PATH=$(dirname $(x86_64-w64-mingw32-gcc -print-libgcc-file-name))
MINGW_LIB_PATH="/usr/x86_64-w64-mingw32/lib"

log "Searching for DLLs in: $GCC_LIB_PATH and $MINGW_LIB_PATH"

# Grep for DLLs, normalize names, and copy them if they exist.
x86_64-w64-mingw32-objdump -p "$DIST_DIR/dlf_parser_helper.exe" |
  grep 'DLL Name:' |
  awk '{print $3}' |
  sort -u |
  while read dll_name; do
    # Use a case statement for pattern matching
    case "$dll_name" in
      "libdivecomputer"*)
        # Already copied, so we skip.
        continue
        ;;
      "KERNEL32.dll"|"USER32.dll"|"ADVAPI32.dll"|"SHELL32.dll"|"msvcrt.dll"|"WS2_32.dll")
        log "Ignoring system DLL: $dll_name"
        ;;
      *)
        log "Found dependency: $dll_name. Searching for it..."
        # Search in the discovered MinGW paths.
        dll_path=$(find "$GCC_LIB_PATH" "$MINGW_LIB_PATH" -name "$dll_name" -print -quit 2>/dev/null)
        if [ -n "$dll_path" ]; then
          cp "$dll_path" "$DIST_DIR/"
          log "Copied $dll_name from $dll_path"
        else
          log "WARNING: Could not find DLL: $dll_name. The executable may not run."
        fi
        ;;
    esac
  done

log "DLL collection complete."

log "Verifying final artifacts in dist directory..."
ls -lR "$BASE_DIR/dist"

log "Build artifacts are located in: $DIST_DIR"
log "Build process finished successfully!"