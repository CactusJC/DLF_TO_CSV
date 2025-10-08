# dlf_parser_helper for Windows - User Guide

This guide explains how to use the `dlf_parser_helper.exe` tool and the provided Python wrapper script (`libdc_json_to_csv.py`) on a Windows system.

## Requirements

1.  **Python 3:** You need Python 3 installed on your system.
    *   Download it from the [official Python website](https://www.python.org/downloads/).
    *   During installation, make sure to check the box that says **"Add Python to PATH"**.

2.  **Project Files:** You will need the following files in the same directory on your Windows machine:
    *   `dlf_parser_helper.exe`
    *   `libdivecomputer.dll`
    *   Any other `.dll` files included in the distribution package.
    *   `libdc_json_to_csv.py` (the Python wrapper script from the `tools/` directory).

## Instructions

1.  **Prepare Your Files:**
    *   Create a new folder on your computer (e.g., `C:\dlf-tools`).
    *   Copy all the files from the `dist/win-x86_64` folder (the `.exe` and `.dll` files) into this new folder.
    *   Copy the `libdc_json_to_csv.py` script (from the `tools` directory of the original project) into this same folder.

2.  **Open Command Prompt:**
    *   Navigate to the folder you created. A simple way is to open the folder in File Explorer, click on the address bar, type `cmd`, and press Enter. This will open a Command Prompt window directly in that directory.

3.  **Run the Conversion:**
    You can now use the Python script to convert your `.dlf` dive log files.

    **Example: Converting a DLF file to CSV**

    If you have a dive log file named `my_dive.dlf` in the same folder, run the following command:

    ```sh
    python libdc_json_to_csv.py --helper dlf_parser_helper.exe --out my_dive.csv my_dive.dlf
    ```

    *   `--helper dlf_parser_helper.exe`: Tells the script to use the Windows executable.
    *   `--out my_dive.csv`: Specifies the name of the output CSV file.
    *   `my_dive.dlf`: The input `.dlf` file.

    After the command finishes, you will find a `my_dive.csv` file in the folder, which you can open with Microsoft Excel or any other spreadsheet program.

    **Example: Converting a DLF file to SSRF**

    To convert to SSRF format instead, use the `--ssrf-out` argument:

     ```sh
    python libdc_json_to_csv.py --helper dlf_parser_helper.exe --ssrf-out my_dive.ssrf my_dive.dlf
    ```

This will produce `my_dive.ssrf` in the same directory.