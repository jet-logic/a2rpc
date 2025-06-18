#!/usr/bin/env python3
from shutil import rmtree
import unittest
import subprocess
import time
from pathlib import Path
from typing import List
import tempfile
import requests


class TestAria2RPC(unittest.TestCase):
    TEST_DIR = Path(tempfile.mkdtemp())

    @classmethod
    def setUpClass(cls):
        cls.TEST_DIR.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        rmtree(str(cls.TEST_DIR))

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

    # @unittest.skip("Enable to test download commands")
    def test_01(self):
        add_cmd = [
            "python3",
            "-m",
            "a2rpc",
            "--port",
            6888,
            "--rpc-secret",
            "atatatata",
            "start",
            "--",
            "--max-concurrent-downloads",
            8,
        ]
        result = self._run_command(add_cmd, "Start aria")
        self.assertEqual(result.returncode, 0)
        input = self.TEST_DIR / "input.txt"
        input.write_text(
            rf"""
                dir={self.TEST_DIR}
https://releases.ubuntu.com/noble/ubuntu-24.04.2-netboot-amd64.tar.gz
    out=netboot-amd64.tar.gz
https://releases.ubuntu.com/noble/ubuntu-24.04.2-desktop-amd64.iso.torrent
    follow-torrent=mem
https://releases.ubuntu.com/noble/ubuntu-24.04.2-wsl-amd64.wsl https://releases.ubuntu.com/noble/ubuntu-24.04.2-wsl-amd64.manifest
    dir={self.TEST_DIR.joinpath("wsl")}
        """
        )
        # Add download
        add_cmd = [
            "python3",
            "-m",
            "a2rpc",
            "--rpc-secret",
            "atatatata",
            "--rpc-url",
            "http://localhost:6888/jsonrpc",
            "input",
            input,
        ]
        result = self._run_command(add_cmd, "Adding test download")
        self.assertEqual(result.returncode, 0)
        # Get the GID from output
        gids = [x.split()[-1] for x in result.stdout.splitlines()]
        self.assertTrue(gids)
        for gid in gids:
            self.assertTrue(len(gid) > 5)  # Basic GID format check
        #
        time.sleep(5)
        print(gids)
        #
        self._run_command(["find", self.TEST_DIR], f"List {self.TEST_DIR}")

        # List downloads
        list_cmd = [
            "python3",
            "-m",
            "a2rpc",
            "--rpc-secret",
            "atatatata",
            "--rpc-url",
            "http://localhost:6888/jsonrpc",
            "list",
            "--debug",
        ]
        result = self._run_command(list_cmd, "Listing downloads")
        self.assertEqual(result.returncode, 0)
        self.assertIn(gid, result.stdout)
        #
        self.assertTrue(self.TEST_DIR.joinpath("netboot-amd64.tar.gz").is_file())
        self.assertTrue(self.TEST_DIR.joinpath("ubuntu-24.04.2-desktop-amd64.iso").is_file())
        self.assertTrue(self.TEST_DIR.joinpath("wsl", "ubuntu-24.04.2-wsl-amd64.manifest").is_file())
        # Remove download
        # for gid in gids:
        #     remove_cmd = [
        #         "python3",
        #         "-m",
        #         "a2rpc",
        #         "--rpc-secret",
        #         "atatatata",
        #         "--rpc-url",
        #         "http://localhost:6888/jsonrpc",
        #         "remove",
        #         gid,
        #     ]
        #     result = self._run_command(remove_cmd, "Removing download")
        #     self.assertEqual(result.returncode, 0)

        # Run shutdown command
        shutdown_cmd = ["python3", "-m", "a2rpc", "--rpc-url", "http://localhost:6888/jsonrpc", "shutdown"]
        result = self._run_command(shutdown_cmd, "Shutting down server (no rpc-secret)")
        self.assertNotEqual(result.returncode, 0)
        #
        shutdown_cmd = [
            "python3",
            "-m",
            "a2rpc",
            "--rpc-secret",
            "atatatata",
            "--rpc-url",
            "http://localhost:6888/jsonrpc",
            "shutdown",
        ]
        result = self._run_command(shutdown_cmd, "Shutting down server (with rpc-secret)")
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
