#!/usr/bin/env python3
"""
ccrun proxy — sits between Claude Code and LM Studio's Anthropic-compatible
/v1/messages endpoint and rewrites requests so the local backend accepts them.

Fixes applied to POST /v1/messages:
  1. Anchors every JSON-Schema `pattern` in tool input schemas to ^...$
     (llama.cpp's grammar converter rejects unanchored patterns).
  2. Drops replayed `thinking` / `redacted_thinking` blocks.
  3. Converts `document` (base64 PDF) blocks into something LM Studio accepts:
       - text  : extracted PDF text (default for text PDFs)
       - image : rasterized pages as PNG image blocks
       - hybrid: text if rich enough, else image fallback (default)
  4. Flattens `tool_result` blocks whose `content` is an array (LM Studio only
     accepts string tool_result content) into plain text.
  5. Strips any other unknown content-block type to a text placeholder.

Everything else is proxied transparently (streaming preserved).

Env vars (all optional):
  CCRUN_UPSTREAM        upstream base URL          (default http://127.0.0.1:1234)
  CCRUN_PROXY_PORT      port to listen on          (default 8765)
  CCRUN_PDF_MODE        text | image | hybrid      (default hybrid)
  CCRUN_PDF_MAX_PAGES   max pages when rasterizing (default 10)
  CCRUN_PDF_DPI         DPI when rasterizing       (default 150)
  CCRUN_PDF_TEXT_MIN    min chars to keep text in hybrid mode (default 40)
"""

import base64
import json
import logging
import os

from aiohttp import ClientSession, ClientTimeout, web

UPSTREAM = os.environ.get("CCRUN_UPSTREAM", "http://127.0.0.1:1234").rstrip("/")
UPSTREAM_SMALL = os.environ.get("CCRUN_UPSTREAM_SMALL", "").rstrip("/")
SMALL_NAME = os.environ.get("CCRUN_SMALL_NAME", "small-fast")
PORT = int(os.environ.get("CCRUN_PROXY_PORT", "8765"))
PDF_MODE = os.environ.get("CCRUN_PDF_MODE", "hybrid").lower()
PDF_MAX_PAGES = int(os.environ.get("CCRUN_PDF_MAX_PAGES", "10"))
PDF_DPI = int(os.environ.get("CCRUN_PDF_DPI", "150"))
PDF_TEXT_MIN = int(os.environ.get("CCRUN_PDF_TEXT_MIN", "40"))

# Blocchi che LM Studio accetta e che vanno lasciati passare invariati.
# text/image/tool_result sono lato user; tool_use e' lato assistant (le tool call):
# se NON lo includi, le tool call vengono rimosse e i tool_result restano orfani
# -> "Tool result message must immediately follow assistant tool use message".
# tool_reference: usato dalla tool search di Claude Code (ENABLE_TOOL_SEARCH).
# Il client li manda DENTRO i tool_result (content array) quando "trova" un tool
# deferito; senza inoltrarli, l'handshake si rompe e la chat resta idle.
ALLOWED_BLOCKS = {"text", "image", "tool_use", "tool_result", "tool_reference"}

logging.basicConfig(level=logging.INFO, format="[ccrun-proxy] %(message)s")
log = logging.getLogger("ccrun")

try:
    import fitz  # PyMuPDF
    HAVE_FITZ = True
except Exception:  # pragma: no cover
    HAVE_FITZ = False
    log.warning("PyMuPDF non disponibile: i PDF verranno rimossi, non convertiti.")


# --------------------------------------------------------------------------- #
# Transformations
# --------------------------------------------------------------------------- #
def anchor_patterns(node):
    """Recursively ensure every `pattern` string is anchored with ^...$."""
    if isinstance(node, dict):
        pat = node.get("pattern")
        if isinstance(pat, str):
            if not pat.startswith("^"):
                pat = "^" + pat
            if not pat.endswith("$"):
                pat = pat + "$"
            node["pattern"] = pat
        for value in node.values():
            anchor_patterns(value)
    elif isinstance(node, list):
        for item in node:
            anchor_patterns(item)


def pdf_to_blocks(b64_data):
    """Turn a base64 PDF into LM-Studio-acceptable blocks per PDF_MODE."""
    if not HAVE_FITZ:
        return [{"type": "text", "text": "[PDF rimosso: PyMuPDF non installato]"}]
    try:
        doc = fitz.open(stream=base64.b64decode(b64_data), filetype="pdf")
    except Exception as exc:
        return [{"type": "text", "text": f"[PDF non leggibile: {exc}]"}]

    if PDF_MODE != "image":
        text = "\n\n".join(page.get_text() for page in doc)
        if PDF_MODE == "text" or len(text.strip()) >= PDF_TEXT_MIN:
            return [{"type": "text", "text": "[Testo estratto dal PDF]\n" + text}]

    # image mode, or hybrid with too little text -> rasterize pages
    blocks = []
    for page in list(doc)[:PDF_MAX_PAGES]:
        pix = page.get_pixmap(dpi=PDF_DPI)
        png_b64 = base64.b64encode(pix.tobytes("png")).decode()
        blocks.append({
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": png_b64},
        })
    return blocks or [{"type": "text", "text": "[PDF vuoto]"}]


def sanitize_block(block):
    """Return a list of blocks (a block may expand or disappear)."""
    btype = block.get("type")

    if btype == "document":
        src = block.get("source", {})
        if src.get("type") == "base64" and src.get("media_type") == "application/pdf":
            return pdf_to_blocks(src.get("data", ""))
        return [{"type": "text", "text": "[documento non-PDF rimosso]"}]

    if btype in ("thinking", "redacted_thinking"):
        return []

    if btype == "tool_result":
        content = block.get("content")
        if isinstance(content, list):
            # i tool_reference della tool search vanno preservati come array:
            # se ce n'e' almeno uno, NON appiattire in stringa (la romperebbe)
            if any(isinstance(s, dict) and s.get("type") == "tool_reference" for s in content):
                kept = [s for s in content
                        if isinstance(s, dict) and s.get("type") in ("text", "tool_reference")]
                preserved = dict(block)
                preserved["content"] = kept
                return [preserved]
            parts = []
            for sub in content:
                if isinstance(sub, str):
                    parts.append(sub)
                elif isinstance(sub, dict) and sub.get("type") == "text":
                    parts.append(sub.get("text", ""))
                elif isinstance(sub, dict):
                    parts.append(f"[blocco '{sub.get('type')}' nel tool_result rimosso]")
            flattened = dict(block)
            flattened["content"] = "\n".join(parts)
            return [flattened]
        return [block]

    if btype in ALLOWED_BLOCKS:
        return [block]

    return [{"type": "text", "text": f"[blocco '{btype}' rimosso]"}]


def transform_body(body):
    stats = {"patterns": 0, "pdf": 0, "thinking": 0, "other": 0}

    for tool in body.get("tools") or []:
        before = json.dumps(tool.get("input_schema", {}))
        anchor_patterns(tool.get("input_schema", {}))
        if json.dumps(tool.get("input_schema", {})) != before:
            stats["patterns"] += 1

    for msg in body.get("messages") or []:
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        new_content = []
        for block in content:
            if not isinstance(block, dict):
                new_content.append(block)
                continue
            t = block.get("type")
            result = sanitize_block(block)
            if t == "document":
                stats["pdf"] += 1
            elif t in ("thinking", "redacted_thinking"):
                stats["thinking"] += 1
            elif t not in ALLOWED_BLOCKS:
                stats["other"] += 1
            new_content.extend(result)
        msg["content"] = new_content or [{"type": "text", "text": ""}]

    if any(stats.values()):
        log.info("transform: %s", {k: v for k, v in stats.items() if v})
    return body


# --------------------------------------------------------------------------- #
# Proxy plumbing
# --------------------------------------------------------------------------- #
HOP_BY_HOP = {"host", "content-length", "accept-encoding", "connection"}
RESP_SKIP = {"content-length", "transfer-encoding", "content-encoding", "connection"}


async def handle(request):
    body = await request.read()
    target = UPSTREAM

    if request.method == "POST" and request.path.endswith("/v1/messages"):
        try:
            data = json.loads(body)
            if UPSTREAM_SMALL and str(data.get("model", "")).startswith(SMALL_NAME):
                target = UPSTREAM_SMALL
            body = json.dumps(transform_body(data)).encode()
        except Exception as exc:
            log.warning("transform saltato (%s), inoltro grezzo", exc)

    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in HOP_BY_HOP}
    url = target + request.path_qs

    timeout = ClientTimeout(total=None, sock_connect=30)
    try:
        async with ClientSession(timeout=timeout) as session:
            async with session.request(request.method, url, data=body,
                                       headers=headers) as upstream:
                resp_headers = {k: v for k, v in upstream.headers.items()
                                if k.lower() not in RESP_SKIP}
                resp = web.StreamResponse(status=upstream.status, headers=resp_headers)
                await resp.prepare(request)
                async for chunk in upstream.content.iter_any():
                    await resp.write(chunk)
                await resp.write_eof()
                return resp
    except Exception as exc:
        log.error("upstream non raggiungibile: %s", exc)
        return web.json_response(
            {"type": "error", "error": {"type": "api_error",
                                         "message": f"ccrun proxy: {exc}"}},
            status=502,
        )


def main():
    log.info("upstream=%s  small=%s  listen=127.0.0.1:%d  pdf_mode=%s", UPSTREAM, UPSTREAM_SMALL or "-", PORT, PDF_MODE)
    app = web.Application(client_max_size=1024 ** 3)  # 1 GB, base64 PDF puo' essere grande
    app.router.add_route("*", "/{tail:.*}", handle)
    web.run_app(app, host="127.0.0.1", port=PORT, print=None)


if __name__ == "__main__":
    main()
