# Developer Build Manual: Cross-Compiling for Windows on Ubuntu

This document provides a detailed, step-by-step guide for developers to cross-compile the `dlf_parser_helper` for Windows x86_64 on an Ubuntu system.

## 1. Overview

The process involves these main stages:
1.  **Environment Setup:** Installing the necessary tools and dependencies on Ubuntu.
2.  **Building `libdivecomputer`:** Cross-compiling this core dependency as a Windows DLL.
3.  **Building `dlf_parser_helper`:** Compiling the main tool and linking it against the new `libdivecomputer` DLL.
4.  **Packaging:** Collecting the final executable and all required DLLs into a distribution directory.

All these steps are automated by the `build-cross-ubuntu.sh` script. This manual explains how to use the script and what it does.

## 2. Prerequisites

You need a Debian-based system (e.g., Ubuntu 24.04) with `sudo` access.

## 3. How to Run the Automated Build

The entire build process is handled by the `build-cross-ubuntu.sh` script.

1.  **Navigate to the `windows` directory:**
    ```sh
    cd /path/to/your/project/windows
    ```

2.  **Run the build script:**
    ```sh
    ./build-cross-ubuntu.sh
    ```

The script will perform all the necessary steps, including installing dependencies (which requires `sudo`), cloning and building `libdivecomputer`, building the helper, and packaging the artifacts.

**Expected Log Output:**
The script will print its progress. A successful run will look something like this:
```
--- Starting the Windows cross-compile build process ---
--- Cleaning previous build artifacts... ---
--- Verifying build environment... ---
All required dependency checks passed.
--- Installing required system packages (requires sudo)... ---
[apt-get output]
--- Cloning libdivecomputer from https://github.com/libdivecomputer/libdivecomputer.git... ---
Cloning into '/tmp/libdivecomputer_build_XXXXXX/libdivecomputer'...
...
--- Configuring libdivecomputer for Windows (x86_64)... ---
checking for a BSD-compatible install... /usr/bin/install -c
...
configure: creating ./config.status
--- Building libdivecomputer... ---
make[1]: Entering directory '/tmp/libdivecomputer_build_XXXXXX/libdivecomputer'
...
make[1]: Leaving directory '/tmp/libdivecomputer_build_XXXXXX/libdivecomputer'
--- Building dlf_parser_helper.exe... ---
Successfully built dlf_parser_helper.exe
--- Collecting required DLLs... ---
Copied libdivecomputer.dll
--- Analyzing dlf_parser_helper.exe for other DLL dependencies... ---
Searching for DLLs in /usr/x86_64-w64-mingw32/lib and /lib/x86_64-w64-mingw32/...
Found dependency: KERNEL32.dll. Searching for it...
...
--- DLL collection complete. ---
--- Build artifacts are located in: /path/to/project/windows/dist/win-x86_64 ---
--- Build process finished successfully! ---
--- Cleaning up temporary build directory... ---
```

Upon completion, the `windows/dist/win-x86_64` directory will contain `dlf_parser_helper.exe` and all its required `.dll` files.

## 4. How to Verify Artifacts

### Checking Dependencies
To ensure all required DLLs were correctly identified and packaged, you can use `x86_64-w64-mingw32-objdump`.

1.  **Run `objdump` on the generated executable:**
    ```sh
    x86_64-w64-mingw32-objdump -p windows/dist/win-x86_64/dlf_parser_helper.exe | grep 'DLL Name:'
    ```
    This will list all DLLs the executable depends on.

2.  **Verify that each listed DLL exists in the `dist` directory** (except for core Windows system DLLs like `KERNEL32.dll`, `USER32.dll`, etc., which are part of every Windows system).

    You should see `libdivecomputer.dll` and potentially others like `libgcc_s_seh-1.dll` or `libwinpthread-1.dll`.

### Testing with Wine (Optional)
If you have `wine` installed (`sudo apt install wine64`), you can perform a basic runtime test on Linux.

1.  **Navigate to the output directory:**
    ```sh
    cd windows/dist/win-x86_64/
    ```

2.  **Run the executable via Wine:**
    (You will need a sample `.dlf` file for this test).
    ```sh
    wine dlf_parser_helper.exe /path/to/sample.dlf
    ```
    If the command outputs JSON data without errors about missing DLLs, the packaging was successful.

## 5. Packaging the Build

To create a distributable zip archive from the build artifacts, use the `package-windows.sh` script.

1.  **Make sure you have run the build script first.**

2.  **Run the packaging script:**
    ```sh
    ./package-windows.sh
    ```
    This will create a timestamped `.zip` file inside the `windows/dist/` directory, for example: `windows/dist/dlf_parser_helper_win-x86_64_20231027-123456.zip`.

## 6. Troubleshooting

*   **`command not found: x86_64-w64-mingw32-gcc`**: The `mingw-w64` package is not installed or not in your `PATH`. The build script should handle this automatically, but you can install it manually with `sudo apt install mingw-w64`.
*   **`configure: error: ...` during `libdivecomputer` build**: This usually indicates a missing build tool like `autoconf`, `automake`, or `libtool`. The build script should install these.
*   **`.dll` not found errors when running with Wine**: This means a required DLL was not copied to the `dist` directory. Check the `objdump` output and ensure the DLL collection logic in the build script is working correctly and the DLL exists in the MinGW sysroot on your system.