#!/usr/bin/env python3
"""MCP stdio server per le approvazioni interattive di ccllrun Studio.

Claude Code headless (`claude -p`) non ha un prompt di approvazione: con
`--permission-prompt-tool mcp__studioperm__approve` chiama questo tool ogni
volta che un comando richiede il permesso. Il tool inoltra la richiesta al
server di Studio (/api/perm/ask), che la mostra in chat e resta in attesa
della risposta dell'utente (Consenti / Consenti sempre / Nega).

Protocollo MCP: JSON-RPC newline-delimited su stdio. Solo stdlib.
"""
import json
import os
import sys
import urllib.request

PORT = int(os.environ.get("STUDIO_PORT", "8770"))


def ask(args):
    payload = json.dumps({
        "tool_name": args.get("tool_name") or "",
        "input": args.get("input") or {},
        "cwd": os.getcwd(),          # claude gira nella cartella della chat
    }).encode()
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/api/perm/ask", data=payload,
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return json.load(r)
    except Exception as exc:
        return {"behavior": "deny", "message": f"Studio non raggiungibile: {exc}"}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except ValueError:
            continue
        mid, method = msg.get("id"), msg.get("method")
        if method == "initialize":
            out = {"jsonrpc": "2.0", "id": mid, "result": {
                "protocolVersion": (msg.get("params") or {}).get("protocolVersion", "2024-11-05"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "studioperm", "version": "1.0"}}}
        elif method == "tools/list":
            out = {"jsonrpc": "2.0", "id": mid, "result": {"tools": [{
                "name": "approve",
                "description": "Chiede all'utente di ccllrun Studio l'approvazione di un tool",
                "inputSchema": {"type": "object", "properties": {
                    "tool_name": {"type": "string"},
                    "input": {"type": "object"},
                    "tool_use_id": {"type": "string"}}}}]}}
        elif method == "tools/call":
            res = ask((msg.get("params") or {}).get("arguments") or {})
            out = {"jsonrpc": "2.0", "id": mid, "result": {
                "content": [{"type": "text", "text": json.dumps(res)}]}}
        elif mid is None:
            continue                  # notification (es. notifications/initialized)
        else:
            out = {"jsonrpc": "2.0", "id": mid,
                   "error": {"code": -32601, "message": f"metodo sconosciuto: {method}"}}
        sys.stdout.write(json.dumps(out) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
