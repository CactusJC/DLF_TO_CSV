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

        # Make sure the reference XML exists
        if not os.path.exists(self.reference_xml):
            self.fail(f"Reference XML file not found at {self.reference_xml}")

    def test_c_helper_json_output(self):
        """Tests if the C helper produces JSON that matches the reference XML."""
        command = [self.helper_path, self.input_dlf]
        env = {"LD_LIBRARY_PATH": "/usr/local/lib"}
        result = subprocess.run(command, capture_output=True, text=True, check=True, env=env)
        json_data = json.loads(result.stdout)

        tree = ET.parse(self.reference_xml)
        root = tree.getroot()
        xml_samples = root.findall('.//sample')

        self.assertEqual(len(json_data['samples']), len(xml_samples), "Number of samples does not match")

        for i, json_sample in enumerate(json_data['samples']):
            xml_sample = xml_samples[i]

            json_time_parts = json_sample['time'].split(':')
            json_time_seconds = int(json_time_parts[0]) * 60 + int(json_time_parts[1])

            xml_time_str = xml_sample.find('time').text
            xml_time_parts = xml_time_str.split(':')
            xml_time_seconds = int(xml_time_parts[0]) * 60 + int(xml_time_parts[1])

            self.assertEqual(json_time_seconds, xml_time_seconds, f"Time mismatch at sample {i+1}")

            json_depth = float(json_sample['depth'])
            xml_depth_element = xml_sample.find('depth')
            if xml_depth_element is not None:
                xml_depth = float(xml_depth_element.text)
                self.assertAlmostEqual(json_depth, xml_depth, delta=0.02, msg=f"Depth mismatch at sample {i+1}")

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
        env = {"LD_LIBRARY_PATH": "/usr/local/lib"}
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
        env = {"LD_LIBRARY_PATH": "/usr/local/lib"}
        subprocess.run(command, check=True, env=env)

        self.assertTrue(os.path.exists(self.output_ssrf))

        try:
            ET.parse(self.output_ssrf)
        except ET.ParseError as e:
            self.fail(f"SSRF file is not well-formed XML: {e}")

if __name__ == "__main__":
    unittest.main()
