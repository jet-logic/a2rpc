#!/bin/env python3
from time import sleep
from typing import List
from unittest import TestCase, main
from subprocess import CompletedProcess, run, Popen


class TestExtra(TestCase):
    @staticmethod
    def _run_command(args: List, description: str = "") -> CompletedProcess:
        """Run a shell command with logging"""
        print(f"\n=== Executing: {description} ===")
        print(f"Command: {' '.join(str(a) for a in args)}")

        result = run([str(a) for a in args], capture_output=True, text=True)  # Convert all args to string

        print(f"Return code: {result.returncode}")
        if result.stdout:
            print(f"stdout:\n{result.stdout}")
        if result.stderr:
            print(f"stderr:\n{result.stderr}")

        return result

    def test_start_shutdown(self):
        p = Popen(["python", "-m", "ariarpcc", "start"])
        sleep(1)
        c = run(["python", "-m", "ariarpcc", "shutdown", "--force"], check=True)
        self.assertEqual(c.returncode, 0)
        p.terminate()
        p.wait(5)


if __name__ == "__main__":
    main()
