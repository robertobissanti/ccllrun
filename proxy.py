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
  CCRUN_UPSTREAM_API    anthropic | openai        (default anthropic)
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
import time

from aiohttp import ClientSession, ClientTimeout, web

UPSTREAM = os.environ.get("CCRUN_UPSTREAM", "http://127.0.0.1:1234").rstrip("/")
UPSTREAM_SMALL = os.environ.get("CCRUN_UPSTREAM_SMALL", "").rstrip("/")
UPSTREAM_API = os.environ.get("CCRUN_UPSTREAM_API", "anthropic").lower()
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


def block_text(block):
    if isinstance(block, str):
        return block
    if not isinstance(block, dict):
        return str(block)
    btype = block.get("type")
    if btype == "text":
        return block.get("text", "")
    if btype == "tool_result":
        return "[tool_result]\n" + str(block.get("content", ""))
    if btype == "tool_use":
        return "[tool_use]\n" + json.dumps(block, ensure_ascii=False)
    if btype == "image":
        return "[image input omitted: upstream OpenAI-compatible MLX server is text-only]"
    return f"[{btype or 'block'} omitted]"


def content_text(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(block_text(block) for block in content).strip()
    return "" if content is None else str(content)


def anthropic_to_openai(body):
    body = transform_body(body)
    messages = []
    system = body.get("system")
    if isinstance(system, str) and system.strip():
        messages.append({"role": "system", "content": system})
    elif isinstance(system, list):
        text = content_text(system)
        if text:
            messages.append({"role": "system", "content": text})

    for msg in body.get("messages") or []:
        role = msg.get("role") or "user"
        if role not in {"system", "user", "assistant"}:
            role = "user"
        messages.append({"role": role, "content": content_text(msg.get("content"))})

    out = {
        "model": "default_model" if UPSTREAM_API == "openai" else (body.get("model") or "local"),
        "messages": messages or [{"role": "user", "content": ""}],
        "stream": bool(body.get("stream")),
    }
    tools = []
    for tool in body.get("tools") or []:
        name = tool.get("name")
        if not name:
            continue
        tools.append({
            "type": "function",
            "function": {
                "name": name,
                "description": tool.get("description") or "",
                "parameters": tool.get("input_schema") or {"type": "object", "properties": {}},
            },
        })
    if tools:
        out["tools"] = tools
        out["tool_choice"] = "auto"
    for src, dst in (
        ("max_tokens", "max_tokens"),
        ("temperature", "temperature"),
        ("top_p", "top_p"),
        ("top_k", "top_k"),
        ("stop_sequences", "stop"),
        ("stop", "stop"),
    ):
        if src in body:
            out[dst] = body[src]
    return out


def openai_message_text(data):
    try:
        msg = data.get("choices", [{}])[0].get("message", {})
        content = msg.get("content", "")
        return content if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
    except Exception:
        return ""


def parse_tool_arguments(raw):
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str) or not raw.strip():
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    except Exception:
        return {"_raw": raw}


def anthropic_tool_id(raw_id, index=0):
    raw = str(raw_id or "")
    if raw.startswith("toolu_"):
        return raw
    return f"toolu_{raw or f'local_{int(time.time() * 1000)}_{index}'}"


def anthropic_message_response(openai_data, model):
    message = {}
    try:
        message = openai_data.get("choices", [{}])[0].get("message", {}) or {}
    except Exception:
        message = {}
    content = []
    text = message.get("content")
    if isinstance(text, str) and text:
        content.append({"type": "text", "text": text})
    for idx, call in enumerate(message.get("tool_calls") or []):
        fn = call.get("function") or {}
        content.append({
            "type": "tool_use",
            "id": anthropic_tool_id(call.get("id"), idx),
            "name": fn.get("name") or f"tool_{idx}",
            "input": parse_tool_arguments(fn.get("arguments")),
        })
    if not content:
        content = [{"type": "text", "text": openai_message_text(openai_data)}]
    usage = openai_data.get("usage") if isinstance(openai_data, dict) else {}
    stop_reason = "tool_use" if any(c.get("type") == "tool_use" for c in content) else "end_turn"
    return {
        "id": str(openai_data.get("id") or "msg_local"),
        "type": "message",
        "role": "assistant",
        "model": model,
        "content": content,
        "stop_reason": stop_reason,
        "stop_sequence": None,
        "usage": {
            "input_tokens": int((usage or {}).get("prompt_tokens") or 0),
            "output_tokens": int((usage or {}).get("completion_tokens") or 0),
        },
    }


def sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n".encode()


def openai_tool_delta_state(tool_calls, delta_calls):
    for call in delta_calls or []:
        idx = int(call.get("index") or 0)
        state = tool_calls.setdefault(idx, {"id": "", "name": "", "arguments": ""})
        if call.get("id"):
            state["id"] += str(call.get("id"))
        fn = call.get("function") or {}
        if fn.get("name"):
            state["name"] += str(fn.get("name"))
        if fn.get("arguments"):
            state["arguments"] += str(fn.get("arguments"))


# --------------------------------------------------------------------------- #
# Proxy plumbing
# --------------------------------------------------------------------------- #
HOP_BY_HOP = {"host", "content-length", "accept-encoding", "connection"}
RESP_SKIP = {"content-length", "transfer-encoding", "content-encoding", "connection"}


async def handle(request):
    if request.method in {"GET", "HEAD"} and request.path == "/health":
        return web.json_response({"status": "ok"})
    if request.method in {"GET", "HEAD"} and request.path == "/props":
        return web.json_response({"backend": UPSTREAM_API, "upstream": UPSTREAM})
    if request.method == "HEAD" and request.path == "/":
        return web.Response(status=200)

    body = await request.read()
    target = UPSTREAM
    path_qs = request.path_qs
    openai_mode = UPSTREAM_API == "openai"
    model = "local"

    if request.method == "POST" and request.path.endswith("/v1/messages"):
        try:
            data = json.loads(body)
            model = str(data.get("model") or model)
            if UPSTREAM_SMALL and str(data.get("model", "")).startswith(SMALL_NAME):
                target = UPSTREAM_SMALL
            if openai_mode:
                path_qs = "/v1/chat/completions"
                body = json.dumps(anthropic_to_openai(data)).encode()
            else:
                body = json.dumps(transform_body(data)).encode()
        except Exception as exc:
            log.warning("transform saltato (%s), inoltro grezzo", exc)

    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in HOP_BY_HOP}
    if openai_mode:
        headers["content-type"] = "application/json"
    url = target + path_qs

    timeout = ClientTimeout(total=None, sock_connect=30)
    try:
        async with ClientSession(timeout=timeout) as session:
            async with session.request(request.method, url, data=body,
                                       headers=headers) as upstream:
                if openai_mode and request.method == "POST" and request.path.endswith("/v1/messages"):
                    if upstream.status >= 400:
                        data = await upstream.read()
                        return web.Response(status=upstream.status, body=data, headers={
                            k: v for k, v in upstream.headers.items() if k.lower() not in RESP_SKIP
                        })
                    if upstream.headers.get("content-type", "").startswith("text/event-stream"):
                        resp = web.StreamResponse(status=200, headers={
                            "content-type": "text/event-stream; charset=utf-8",
                            "cache-control": "no-cache",
                        })
                        await resp.prepare(request)
                        await resp.write(sse("message_start", {
                            "type": "message_start",
                            "message": {"id": "msg_local", "type": "message", "role": "assistant",
                                        "model": model, "content": [], "stop_reason": None,
                                        "stop_sequence": None,
                                        "usage": {"input_tokens": 0, "output_tokens": 0}},
                        }))
                        pending = ""
                        content_index = 0
                        text_started = False
                        tool_calls = {}
                        async for raw in upstream.content:
                            pending += raw.decode(errors="replace")
                            lines = pending.splitlines()
                            pending = "" if pending.endswith(("\n", "\r")) else (lines.pop() if lines else pending)
                            for line in lines:
                                if not line.startswith("data:"):
                                    continue
                                payload = line[5:].strip()
                                if not payload or payload == "[DONE]":
                                    continue
                                try:
                                    chunk = json.loads(payload)
                                    delta_obj = chunk.get("choices", [{}])[0].get("delta", {}) or {}
                                    delta = delta_obj.get("content", "")
                                    openai_tool_delta_state(tool_calls, delta_obj.get("tool_calls"))
                                except Exception:
                                    delta = ""
                                if delta:
                                    if not text_started:
                                        await resp.write(sse("content_block_start", {
                                            "type": "content_block_start", "index": content_index,
                                            "content_block": {"type": "text", "text": ""},
                                        }))
                                        text_started = True
                                    await resp.write(sse("content_block_delta", {
                                        "type": "content_block_delta", "index": content_index,
                                        "delta": {"type": "text_delta", "text": delta},
                                    }))
                        if text_started:
                            await resp.write(sse("content_block_stop", {
                                "type": "content_block_stop", "index": content_index,
                            }))
                            content_index += 1
                        for idx in sorted(tool_calls):
                            call = tool_calls[idx]
                            await resp.write(sse("content_block_start", {
                                "type": "content_block_start", "index": content_index,
                                "content_block": {
                                    "type": "tool_use",
                                    "id": anthropic_tool_id(call.get("id"), idx),
                                    "name": call.get("name") or f"tool_{idx}",
                                    "input": {},
                                },
                            }))
                            await resp.write(sse("content_block_delta", {
                                "type": "content_block_delta", "index": content_index,
                                "delta": {
                                    "type": "input_json_delta",
                                    "partial_json": call.get("arguments") or "{}",
                                },
                            }))
                            await resp.write(sse("content_block_stop", {
                                "type": "content_block_stop", "index": content_index,
                            }))
                            content_index += 1
                        stop_reason = "tool_use" if tool_calls else "end_turn"
                        await resp.write(sse("message_delta", {
                            "type": "message_delta",
                            "delta": {"stop_reason": stop_reason, "stop_sequence": None},
                            "usage": {"output_tokens": 0},
                        }))
                        await resp.write(sse("message_stop", {"type": "message_stop"}))
                        await resp.write_eof()
                        return resp

                    data = await upstream.json(content_type=None)
                    return web.json_response(anthropic_message_response(data, model), status=upstream.status)

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
