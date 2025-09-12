import csv
import json
import os
import subprocess
import unittest
import xml.etree.ElementTree as ET

class TestConversion(unittest.TestCase):
    def setUp(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.helper_path = os.path.join(self.script_dir, "..", "dlf_parser_helper")
        self.script_path = os.path.join(self.script_dir, "..", "libdc_json_to_csv.py")
        self.input_dlf = os.path.join(self.script_dir, "..", "..", "tests", "00000002.dlf")
        self.output_csv = os.path.join(self.script_dir, "..", "..", "tests", "out.csv")
        self.output_ssrf = os.path.join(self.script_dir, "..", "..", "tests", "out.ssrf")
        self.reference_xml = os.path.join(self.script_dir, "..", "..", "tests", "reference.xml")

    def test_c_helper_json_output(self):
        """Tests if the C helper produces valid JSON with expected keys."""
        command = [self.helper_path, self.input_dlf]
        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = "/tmp/libdivecomputer/install/lib"
        result = subprocess.run(command, capture_output=True, text=True, check=True, env=env)

        try:
            json_data = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            self.fail(f"C helper output is not valid JSON: {e}")

        self.assertIn("meta", json_data)
        self.assertIn("samples", json_data)
        self.assertIsInstance(json_data["samples"], list)
        self.assertGreater(len(json_data["samples"]), 0, "No samples were found in the JSON output.")

    def test_python_script_csv_generation(self):
        """Tests if the Python script generates a well-formed CSV file."""
        command = [
            "python3",
            self.script_path,
            "--helper",
            self.helper_path,
            "--out",
            self.output_csv,
            self.input_dlf,
        ]
        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = "/tmp/libdivecomputer/install/lib"
        subprocess.run(command, check=True, env=env)

        self.assertTrue(os.path.exists(self.output_csv))

        with open(self.output_csv, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header, ['index', 'time', 'depth', 'temperature', 'ppo2', 'event'])
            # Check that there is at least one data row
            self.assertTrue(any(reader))

    def test_python_script_ssrf_generation(self):
        """Tests if the Python script generates a well-formed SSRF file."""
        command = [
            "python3",
            self.script_path,
            "--helper",
            self.helper_path,
            "--ssrf-out",
            self.output_ssrf,
            self.input_dlf,
        ]
        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = "/tmp/libdivecomputer/install/lib"
        subprocess.run(command, check=True, env=env)

        self.assertTrue(os.path.exists(self.output_ssrf))

        try:
            ET.parse(self.output_ssrf)
        except ET.ParseError as e:
            self.fail(f"SSRF file is not well-formed XML: {e}")

if __name__ == "__main__":
    unittest.main()
