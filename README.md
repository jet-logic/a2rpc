# Aria2 RPC CLI (a2rpc)

[![PyPI](https://img.shields.io/pypi/v/a2rpc)](https://pypi.org/project/a2rpc/)

A lightweight Python CLI tool to interact with **aria2c's JSON-RPC interface**, designed for scripting and automation.

---

## Features ✨

- **📥 Download Management**  
  Add, pause, resume, or remove downloads via HTTP, Magnet, or torrent links.
- **🖥️ Server Control**  
  Start/shutdown `aria2c` RPC server with custom ports and directories.
- **📋 Batch Processing**  
  Queue multiple downloads from input files with per-URL options.
- **📊 Real-Time Monitoring**  
  List active/waiting/stopped downloads with debug-friendly output.
- **🔒 Secure**  
  Supports RPC secret tokens for authenticated access.

---

## Installation

### Prerequisites

- `aria2c` installed ([Download aria2](https://aria2.github.io/))

### Via pip

```bash
pip install a2rpc
```

### Manual

```bash
git clone https://github.com/jet-logic/a2rpc
cd a2rpc
pip install .
```

---

## Usage

### Basic Commands

| Command             | Description      | Example                              |
| ------------------- | ---------------- | ------------------------------------ |
| `a2rpc start`       | Start RPC server | `a2rpc start --port 6800`            |
| `a2rpc add <URI>`   | Add a download   | `a2rpc add "magnet:?xt=..." -d ~/dl` |
| `a2rpc list`        | List downloads   | `a2rpc list --debug`                 |
| `a2rpc pause <GID>` | Pause a download | `a2rpc pause abc123`                 |
| `a2rpc shutdown`    | Shutdown server  | `a2rpc shutdown --force`             |

### Advanced: Batch Downloads

1. Create an input file (`downloads.txt`):
   ```plaintext
   https://example.com/file1.iso
       dir=/mnt/downloads
   https://example.com/file2.zip
       out=backup.zip
   ```
2. Run:
   ```bash
   a2rpc input downloads.txt
   ```

---

## Configuration

### Global Flags

| Flag           | Description          | Default                         |
| -------------- | -------------------- | ------------------------------- |
| `--rpc-url`    | RPC server URL       | `http://localhost:6800/jsonrpc` |
| `--rpc-secret` | Authentication token | None                            |

Example:

```bash
a2rpc --rpc-secret mytoken add "https://example.com/large-file.mp4"
```

---

## Examples

### 1. Download with Custom Options

```bash
a2rpc add "https://ubuntu.com/24.04.iso" \
  --dir ~/Downloads \
  --out ubuntu-latest.iso \
  -s "max-connection-per-server=16"
```

### 2. Debug Active Downloads

```bash
a2rpc list --debug  # Shows detailed YAML output
```

### 3. Automate with Scripts

```python
import subprocess
subprocess.run(["a2rpc", "add", "magnet:?xt=..."])
```
