#!/bin/bash
# Installation script for dlf-to-csv tools.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "### Building and installing libdivecomputer ###"

# Clone libdivecomputer if it doesn't exist
if [ -d "/tmp/libdivecomputer" ]; then
    echo "--> libdivecomputer source directory already exists. Skipping clone."
else
    echo "--> Cloning libdivecomputer..."
    git clone https://github.com/libdivecomputer/libdivecomputer.git /tmp/libdivecomputer
fi

# Build and install libdivecomputer
echo "--> Configuring and building libdivecomputer..."
cd /tmp/libdivecomputer
autoreconf --install
./configure --prefix=/tmp/libdivecomputer/install
make
make install

# Return to the original directory
echo "--> Returning to project root..."
cd -

# Build the dlf_parser_helper
echo "### Building dlf_parser_helper ###"
export PKG_CONFIG_PATH=/tmp/libdivecomputer/install/lib/pkgconfig
make -C tools

echo ""
echo "### Installation Complete! ###"
echo "The executable is available at: tools/dlf_parser_helper"
echo "You can now use the python script to convert files."