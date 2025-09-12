import argparse
import csv
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

def generate_ssrf(data, output_file):
    """Generates a Subsurface .ssrf file from the dive data."""

    # Create the root element
    root = ET.Element("divelog")

    # Create the settings element
    settings = ET.SubElement(root, "settings")
    ET.SubElement(settings, "divecomputer", id=data['meta']['divecomputer']['model'])

    # Create the dive element
    dive = ET.SubElement(root, "dive")

    # Add dive metadata
    dive.set("number", "1")
    dive.set("date", data['meta']['date'])
    dive.set("time", data['meta']['time'])
    dive.set("duration", data['meta']['duration'])

    # Add cylinder info
    cylinder = ET.SubElement(dive, "cylinder")
    cylinder.set("size", str(data['meta']['cylinder']['size_l']) + " l")
    cylinder.set("workpressure", str(data['meta']['cylinder']['work_pressure_bar']) + " bar")

    # Add divecomputer info
    divecomputer = ET.SubElement(dive, "divecomputer")
    divecomputer.set("model", data['meta']['divecomputer']['model'])
    divecomputer.set("serial", data['meta']['divecomputer']['serial'])

    # Add samples
    for sample in data['samples']:
        s = ET.SubElement(dive, "sample")
        s.set("time", sample['time'])
        s.set("depth", str(sample['depth']) + " m")
        if 'temperature' in sample and sample['temperature'] is not None:
            s.set("temp", str(sample['temperature']) + " C")
        if 'ppo2' in sample and sample['ppo2'] is not None:
            s.set("ppo2", str(sample['ppo2']))
        if 'event' in sample and sample['event'] is not None:
            s.set("event", sample['event'])

    # Create a pretty-printed XML string
    xml_str = ET.tostring(root, 'utf-8')
    pretty_xml_str = minidom.parseString(xml_str).toprettyxml(indent="  ")

    with open(output_file, 'w') as f:
        f.write(pretty_xml_str)


def main():
    parser = argparse.ArgumentParser(description="Convert Divesoft DLF files to CSV or SSRF using dlf_parser_helper.")
    parser.add_argument("--helper", required=True, help="Path to the dlf_parser_helper executable.")
    parser.add_argument("--out", help="Path to the output CSV file.")
    parser.add_argument("--ssrf-out", help="Path to the output SSRF file.")
    parser.add_argument("input_dlf", help="Path to the input DLF file.")

    args = parser.parse_args()

    if not args.out and not args.ssrf_out:
        print("Error: At least one of --out or --ssrf-out must be specified.", file=sys.stderr)
        sys.exit(1)

    try:
        command = [args.helper, args.input_dlf]
        env = {"LD_LIBRARY_PATH": "/usr/local/lib"}
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            env=env
        )
        json_output = result.stdout
    except FileNotFoundError:
        print(f"Error: Helper executable not found at '{args.helper}'", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error running helper process:", file=sys.stderr)
        print(f"  Command: {' '.join(e.cmd)}", file=sys.stderr)
        print(f"  Return code: {e.returncode}", file=sys.stderr)
        print(f"  Stderr: {e.stderr}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(json_output)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON received from helper: {e}", file=sys.stderr)
        print("------- Helper Output -------", file=sys.stderr)
        print(json_output, file=sys.stderr)
        print("-----------------------------", file=sys.stderr)
        sys.exit(1)

    # Write to CSV if requested
    if args.out:
        try:
            with open(args.out, 'w', newline='') as csvfile:
                if not data.get("samples"):
                    print("Warning: No samples found in the dive data.", file=sys.stderr)
                    return

                header = list(data["samples"][0].keys())

                writer = csv.DictWriter(csvfile, fieldnames=header)
                writer.writeheader()
                writer.writerows(data["samples"])

            print(f"Successfully converted '{args.input_dlf}' to '{args.out}'")

        except IOError as e:
            print(f"Error writing to output file '{args.out}': {e}", file=sys.stderr)
            sys.exit(1)

    # Write to SSRF if requested
    if args.ssrf_out:
        try:
            generate_ssrf(data, args.ssrf_out)
            print(f"Successfully converted '{args.input_dlf}' to '{args.ssrf_out}'")
        except Exception as e:
            print(f"Error generating SSRF file: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
