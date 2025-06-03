#!/bin/env python3
from time import sleep
from unittest import TestCase, main
from subprocess import run, Popen


class TestExtra(TestCase):

    def test_start_shutdown(self):
        p = Popen(["python", "-m", "ariarpcc", "start"])
        sleep(1)
        c = run(["python", "-m", "ariarpcc", "shutdown", "--force"], check=True)
        self.assertEqual(c.returncode, 0)
        p.terminate()
        p.wait(5)


if __name__ == "__main__":
    main()
