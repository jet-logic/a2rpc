#!/usr/bin/env python3
import unittest
import subprocess
import time
from pathlib import Path
from typing import List
import tempfile
import requests


class TestAria2RPC(unittest.TestCase):
    RPC_URL = "http://localhost:6800/jsonrpc"
    TEST_DIR = Path(tempfile.gettempdir(), "test_downloads")
    TEST_FILE_URL = "http://ubuntutym2.u-toyama.ac.jp/xubuntu/25.04/release/xubuntu-25.04-desktop-amd64.iso"  # Large test file

    @classmethod
    def setUpClass(cls):
        cls.TEST_DIR.mkdir(exist_ok=True)
        cls.start_server()

    @classmethod
    def tearDownClass(cls):
        cls.stop_server()
        # Clean up test files
        for f in cls.TEST_DIR.glob("*"):
            f.unlink()
        cls.TEST_DIR.rmdir()

    @classmethod
    def start_server(cls):
        """Start aria2c server for testing"""
        cmd = ["aria2c", "--enable-rpc", "--rpc-listen-port=6800", f"--dir={cls.TEST_DIR}", "--daemon", "--quiet"]
        cls._run_command(cmd, "Starting test server")

    @classmethod
    def stop_server(cls):
        """Stop aria2c server after testing"""
        try:
            cls._run_rpc_command("shutdown")
        except requests.exceptions.ConnectionError:
            pass  # Server already stopped

    @staticmethod
    def _run_command(args: List, description: str = "") -> subprocess.CompletedProcess:
        """Run a shell command with logging"""
        print(f"\n=== Executing: {description} ===")
        print(f"Command: {' '.join(str(a) for a in args)}")

        result = subprocess.run([str(a) for a in args], capture_output=True, text=True)  # Convert all args to string

        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"stdout:\n{result.stdout}")
        if result.stderr:
            print(f"stderr:\n{result.stderr}")

        return result

    @classmethod
    def _run_rpc_command(cls, method: str, params: List = None) -> dict:
        """Make RPC call and return parsed JSON"""
        payload = {"jsonrpc": "2.0", "id": "test", "method": f"aria2.{method}", "params": params or []}
        response = requests.post(cls.RPC_URL, json=payload)
        response.raise_for_status()
        return response.json()

    def _get_active_downloads(self) -> List[str]:
        """Get list of active download GIDs"""
        result = self._run_rpc_command("tellActive")
        return [d["gid"] for d in result["result"]]

    @unittest.skip("Enable to test server control")
    def test_01_server_control(self):
        """Test server start/stop functionality"""
        # Server should be running from setUpClass
        active = self._get_active_downloads()
        self.assertIsInstance(active, list)

        # Test shutdown
        self._run_rpc_command("shutdown")
        time.sleep(5)  # Give server time to stop

        # Verify server stopped
        with self.assertRaises(requests.exceptions.ConnectionError):
            self._run_rpc_command("getVersion")

        # Restart server for other tests
        self.start_server()

    # @unittest.skip("Enable to test download commands")
    def test_02_download_commands(self):
        """Test add/list/remove download commands"""
        # Add download
        add_cmd = ["python3", "-m", "ariarpcc", "add", self.TEST_FILE_URL, f"--dir={self.TEST_DIR}"]
        result = self._run_command(add_cmd, "Adding test download")
        self.assertEqual(result.returncode, 0)
        # Get the GID from output
        output_lines = result.stdout.splitlines()
        gid = output_lines[-1].split()[-1]
        self.assertTrue(len(gid) > 5)  # Basic GID format check
        #
        URL2 = "https://releases.ubuntu.com/noble/ubuntu-24.04.2-desktop-amd64.iso.torrent"
        add_cmd = ["python3", "-m", "ariarpcc", "add", URL2, f"--dir={self.TEST_DIR}"]
        result = self._run_command(add_cmd, "Adding test download")
        self.assertEqual(result.returncode, 0)
        #
        time.sleep(10)
        #
        self._run_command(["find", self.TEST_DIR], f"List {self.TEST_DIR}")

        # List downloads
        list_cmd = ["python3", "-m", "ariarpcc", "list", "--debug"]
        result = self._run_command(list_cmd, "Listing downloads")
        self.assertEqual(result.returncode, 0)
        self.assertIn(gid, result.stdout)

        # Remove download
        remove_cmd = ["python3", "-m", "ariarpcc", "remove", gid]
        result = self._run_command(remove_cmd, "Removing download")
        self.assertEqual(result.returncode, 0)

    # @unittest.skip("Enable to test pause/resume")
    def test_03_pause_resume(self):
        """Test pause and resume functionality"""
        # Add download
        add_result = self._run_command(
            ["python3", "-m", "ariarpcc", "add", self.TEST_FILE_URL], "Adding download for pause test"
        )
        gid = add_result.stdout.split()[-1]

        # Pause download
        pause_cmd = ["python3", "-m", "ariarpcc", "pause", gid]
        pause_result = self._run_command(pause_cmd, "Pausing download")
        self.assertEqual(pause_result.returncode, 0)

        # Verify paused status
        status = self._run_rpc_command("tellStatus", [gid])
        self.assertEqual(status["result"]["status"], "paused")

        # Resume download
        resume_cmd = ["python3", "-m", "ariarpcc", "resume", gid]
        resume_result = self._run_command(resume_cmd, "Resuming download")
        self.assertEqual(resume_result.returncode, 0)

        # Clean up
        self._run_rpc_command("remove", [gid])

    @unittest.skip("Enable to test shutdown")
    def test_04_shutdown(self):
        """Test shutdown command"""
        # First verify server is running
        version = self._run_rpc_command("getVersion")
        self.assertIn("version", version["result"])

        # Run shutdown command
        shutdown_cmd = ["python3", "-m", "ariarpcc", "shutdown"]
        result = self._run_command(shutdown_cmd, "Shutting down server")
        self.assertEqual(result.returncode, 0)

        # Verify server stopped
        time.sleep(5)  # Give server time to stop
        with self.assertRaises(requests.exceptions.ConnectionError):
            self._run_rpc_command("getVersion")

        # Restart server for other tests
        self.start_server()


if __name__ == "__main__":
    unittest.main()
