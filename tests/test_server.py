from unittest import TestCase

from mcp_printer.config import PrinterConfig
from mcp_printer.server import PrinterMcpServer


class ServerTests(TestCase):
    def test_initialize_includes_credit(self) -> None:
        server = PrinterMcpServer([])

        response = server.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})

        self.assertEqual(response["result"]["serverInfo"]["credits"], "Steve Villari and Villocity Labs")

    def test_tools_list_exposes_printer_tools(self) -> None:
        server = PrinterMcpServer([])

        response = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
        tool_names = {tool["name"] for tool in response["result"]["tools"]}

        self.assertIn("printer_upload_gcode", tool_names)
        self.assertIn("printer_emergency_stop", tool_names)

    def test_printer_list_returns_configured_printers(self) -> None:
        server = PrinterMcpServer(
            [
                PrinterConfig(
                    id="bench",
                    name="Bench Printer",
                    type="octoprint",
                    base_url="http://octopi.local",
                    camera_id="printer-cam",
                )
            ]
        )

        response = server.handle(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": "printer_list", "arguments": {}},
            }
        )

        self.assertIn("Bench Printer", response["result"]["content"][0]["text"])
        self.assertIn("printer-cam", response["result"]["content"][0]["text"])
