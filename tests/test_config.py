from pathlib import Path
from unittest import TestCase

from mcp_printer.config import load_config


class ConfigTests(TestCase):
    def test_load_config_parses_supported_printers(self) -> None:
        config = Path(self.create_temp_file())
        config.write_text(
            """
            {
              "printers": [
                {
                  "id": "bench",
                  "name": "Bench Printer",
                  "type": "OctoPrint",
                  "base_url": "http://octopi.local/",
              "api_key_env": "OCTO_KEY",
              "camera_id": "printer-cam"
            }
          ]
        }
            """,
            encoding="utf-8",
        )

        printers = load_config(config)

        self.assertEqual(printers[0].id, "bench")
        self.assertEqual(printers[0].type, "octoprint")
        self.assertEqual(printers[0].base_url, "http://octopi.local")
        self.assertEqual(printers[0].camera_id, "printer-cam")

    def test_load_config_rejects_unsupported_printer_type(self) -> None:
        config = Path(self.create_temp_file())
        config.write_text(
            """
            {
              "printers": [
                {
                  "id": "bench",
                  "name": "Bench Printer",
                  "type": "magic",
                  "base_url": "http://example.local"
                }
              ]
            }
            """,
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "Unsupported printer type"):
            load_config(config)

    def create_temp_file(self) -> str:
        import tempfile

        handle = tempfile.NamedTemporaryFile(delete=False)
        handle.close()
        return handle.name
