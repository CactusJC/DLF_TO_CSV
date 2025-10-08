#!/usr/bin/env bash
set -euo pipefail

# Check for required cross-compilation tools.
command -v x86_64-w64-mingw32-gcc >/dev/null 2>&1 || { echo "ERROR: x86_64-w64-mingw32-gcc not found. Please install the mingw-w64 package." >&2; exit 1; }
command -v pkg-config >/dev/null 2>&1 || { echo "ERROR: pkg-config not found. Please install it." >&2; exit 1; }

echo "All required dependency checks passed."