"""Minimal MCP stdio client for vectorcraft-cli (headless, confined to roots)."""
import json
import subprocess
import sys


class Mcp:
    def __init__(self, binary, read_root, write_root):
        self.p = subprocess.Popen(
            [binary, "mcp", "--automation-read-root", read_root,
             "--automation-write-root", write_root],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=sys.stderr,
            text=True, bufsize=1)
        self.n = 0
        self.request("initialize", {
            "protocolVersion": "2025-06-18", "capabilities": {},
            "clientInfo": {"name": "schlaubi-illustration", "version": "1"}})
        self.notify("notifications/initialized")

    def notify(self, method, params=None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self.p.stdin.write(json.dumps(msg) + "\n")
        self.p.stdin.flush()

    def request(self, method, params=None):
        self.n += 1
        msg = {"jsonrpc": "2.0", "id": self.n, "method": method}
        if params is not None:
            msg["params"] = params
        self.p.stdin.write(json.dumps(msg) + "\n")
        self.p.stdin.flush()
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError("server closed")
            reply = json.loads(line)
            if reply.get("id") == self.n:
                if "error" in reply:
                    raise RuntimeError(f"{method}: {reply['error']}")
                return reply["result"]

    def call(self, name, **args):
        res = self.request("tools/call", {"name": name, "arguments": args})
        texts = [c.get("text", "") for c in res.get("content", []) if c.get("type") == "text"]
        if res.get("isError"):
            raise RuntimeError(f"{name} {json.dumps(args)[:300]}: {' '.join(texts)[:500]}")
        return res, texts

    def close(self):
        self.p.stdin.close()
        self.p.wait(timeout=30)
