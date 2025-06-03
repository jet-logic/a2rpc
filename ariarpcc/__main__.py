#!/usr/bin/env python3
import requests
import subprocess
import shutil
from typing import Optional, List, Dict, Any
from .cliskel import Main, arg, flag


class Aria2RPC(Main):
    """
    A CLI tool to interact with aria2c's RPC interface.
    """

    # Global flags
    rpc_url: str = flag(
        "--rpc-url",
        default="http://localhost:6800/jsonrpc",
        help="Aria2 RPC server URL",
    )
    rpc_secret: Optional[str] = flag("--rpc-secret", help="Aria2 RPC secret token")
    aria2c_path: str = flag("--bin", default="aria2c", help="Path to aria2c executable")

    def _call_rpc(self, method: str, params: List[Any] = None) -> Dict[str, Any]:
        """Make a JSON-RPC request to aria2c."""
        if params is None:
            params = []

        if self.rpc_secret:
            params.insert(0, f"token:{self.rpc_secret}")

        payload = {
            "jsonrpc": "2.0",
            "id": "1",
            "method": f"aria2.{method}",
            "params": params,
        }

        response = requests.post(self.rpc_url, json=payload)
        response.raise_for_status()
        return response.json()


class AddDownload(Aria2RPC):
    """Add a new download."""

    uri: str = arg("URI", help="Download URI (HTTP, Magnet, etc.)")
    output: Optional[str] = flag("-o", "--output", help="Custom output filename")
    dir: Optional[str] = flag("-d", "--dir", help="Download directory")

    def start(self):
        def read_inp(f):
            if f == "-":
                from sys import stdin

                inp = stdin
            else:
                inp = open(f, "r")
            umap = {}
            ucur = None
            udef = {}
            with inp:
                for v in inp:
                    v = v.rstrip()
                    if not v or v.startswith("#"):
                        pass
                    elif v.startswith(" ") or v.startswith("\t"):
                        name, _, value = v.lstrip().partition("=")
                        if value and name:
                            if ucur is None:
                                udef[name] = value
                            else:
                                ucur[name] = value
                    elif v not in umap:
                        umap[v] = ucur = udef.copy()
            return umap

        options = {}
        if self.output:
            options["out"] = self.output
        if self.dir:
            options["dir"] = self.dir

        result = self._call_rpc("addUri", [[self.uri], options])
        print(f"Added download with GID: {result['result']}")


class ListDownloads(Aria2RPC):
    """List active downloads."""

    def start(self):
        active = self._call_rpc("tellActive")["result"]
        waiting = self._call_rpc("tellWaiting", [0, 100])["result"]
        stopped = self._call_rpc("tellStopped", [0, 100])["result"]

        print("\n=== Active Downloads ===")
        for task in active:
            print(
                f"[{task['gid']}] {task['completedLength']}/{task['totalLength']} - {task['files'][0]['path']}"
            )

        print("\n=== Waiting Downloads ===")
        for task in waiting:
            print(
                f"[{task['gid']}] {task['completedLength']}/{task['totalLength']} - {task['files'][0]['path']}"
            )

        print("\n=== Stopped Downloads ===")
        for task in stopped:
            print(
                f"[{task['gid']}] {task['completedLength']}/{task['totalLength']} - {task['files'][0]['path']}"
            )


class RemoveDownload(Aria2RPC):
    """Remove a download by GID."""

    gid: str = arg("GID", help="Download GID to remove")

    def start(self):
        result = self._call_rpc("remove", [self.gid])
        print(f"Removed download: {result['result']}")


class PauseDownload(Aria2RPC):
    """Pause a download by GID."""

    gid: str = arg("GID", help="Download GID to pause")
    all: bool = flag("--all", action="store_true", help="Pause all downloads")

    def start(self):
        if self.all:
            result = self._call_rpc("pauseAll")
            print("Paused all downloads.")
        else:
            result = self._call_rpc("pause", [self.gid])
            print(f"Paused download: {result['result']}")


class ResumeDownload(Aria2RPC):
    """Resume a download by GID."""

    gid: str = arg("GID", help="Download GID to resume")
    all: bool = flag("--all", action="store_true", help="Resume all downloads")

    def start(self):
        if self.all:
            result = self._call_rpc("unpauseAll")
            print("Resumed all downloads.")
        else:
            result = self._call_rpc("unpause", [self.gid])
            print(f"Resumed download: {result['result']}")


class Shutdown(Aria2RPC):
    """Shutdown aria2c."""

    force: bool = flag(
        "--force", action="store_true", help="Force shutdown (no confirmation)"
    )

    def _is_server_running(self) -> bool:
        """Check if the RPC server is running by making a test request."""
        try:
            # Use a simple method that should work even without authentication
            response = requests.get(self.rpc_url, timeout=2)
            print(response.json())
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def start(self):
        # if not self._is_server_running():
        #     print("Error: aria2c RPC server is not running")
        #     return

        # if not self.force:
        #     confirm = input("Are you sure you want to shutdown aria2c? (y/N): ")
        #     if confirm.lower() != "y":
        #         print("Shutdown cancelled.")
        #         return

        try:
            result = self._call_rpc("shutdown")
            print("Shutdown command sent to aria2c.")
        except requests.exceptions.ConnectionError:
            print("Failed to connect to aria2c RPC server - it may already be stopped")
        except Exception as e:
            print(f"Error shutting down aria2c: {e}")


class StartServer(Aria2RPC):
    """Start aria2c RPC server."""

    port: int = flag("-p", "--port", default=6800, help="RPC server port")
    enable_rpc: bool = flag(
        "--enable-rpc",
        action="store_true",
        default=True,
        help="Enable JSON-RPC/XML-RPC server",
    )
    rpc_listen_all: bool = flag(
        "--rpc-listen-all", action="store_true", help="Listen on all network interfaces"
    )
    rpc_allow_origin_all: bool = flag(
        "--rpc-allow-origin-all", action="store_true", help="Allow all origins"
    )
    continue_downloads: bool = flag(
        "--continue", action="store_true", help="Continue interrupted downloads"
    )
    dir: str = flag("-d", "--dir", help="Default download directory")
    daemon: bool = flag("--daemon", action="store_true", help="Run as daemon")

    def start(self):
        if not shutil.which(self.aria2c_path):
            print(f"Error: aria2c not found at '{self.aria2c_path}'")
            return

        cmd = [self.aria2c_path]

        if self.enable_rpc:
            cmd.extend(["--enable-rpc"])
            cmd.extend(["--rpc-listen-port", str(self.port)])

        if self.rpc_listen_all:
            cmd.append("--rpc-listen-all")

        if self.rpc_allow_origin_all:
            cmd.append("--rpc-allow-origin-all")

        if self.continue_downloads:
            cmd.append("--continue")

        if self.dir:
            cmd.extend(["--dir", self.dir])

        if self.daemon:
            cmd.append("--daemon")

        if self.rpc_secret:
            cmd.extend(["--rpc-secret", self.rpc_secret])

        print(f"Starting aria2c with: {' '.join(cmd)}")
        try:
            subprocess.Popen(cmd)
            print(f"aria2c RPC server started on port {self.port}")
        except Exception as e:
            print(f"Failed to start aria2c: {e}")


class Aria2CLI(Aria2RPC):
    """Main CLI interface for aria2c RPC."""

    def sub_args(self):
        yield StartServer(), {"name": "start", "help": "Start aria2c RPC server"}
        yield AddDownload(), {"name": "add", "help": "Add a new download"}
        yield ListDownloads(), {"name": "list", "help": "List active downloads"}
        yield RemoveDownload(), {"name": "remove", "help": "Remove a download"}
        yield PauseDownload(), {"name": "pause", "help": "Pause a download"}
        yield ResumeDownload(), {"name": "resume", "help": "Resume a download"}
        yield Shutdown(), {"name": "shutdown", "help": "Shutdown aria2c"}


def main():
    """CLI entry point."""
    Aria2CLI().main()


__name__ == "__main__" and main()
