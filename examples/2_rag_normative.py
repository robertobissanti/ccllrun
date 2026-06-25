#!/usr/bin/env python3
"""
EXAMPLE 2 — RAG over a large stable corpus (standards, manuals, many
datasheets) using ccllrun's embedding slot (/v1/embeddings through the proxy).

RAG has two separate phases:

  PHASE 1, INDEXING (offline, once per corpus):
    read PDFs -> extract text (PyMuPDF) -> split into chunks ->
    call /v1/embeddings for each chunk -> persist vectors+text.
    This is your preprocessing step, not something the chat model does.
    Add a PDF? Re-index.

  PHASE 2, QUERY (runtime):
    embed the question -> find nearest chunks (math, not LLM reasoning) ->
    paste those chunks into the BIG model prompt. The embedding model never
    answers; it only produces vectors.

USAGE:
    # 1) index a folder offline
    python3 examples/2_rag_normative.py index /percorso/normative
    #    Scanned PDFs (images, no text)? Add --ocr (slow):
    python3 examples/2_rag_normative.py index /percorso/normative --ocr
    #    For Italian standards: brew install tesseract-lang.

    # 2) query at runtime: retrieve chunks and pass them to the big model
    python3 examples/2_rag_normative.py query "protezione di interfaccia CEI 0-21"

REQUIREMENTS:
    - running stack: ccllrun servers
    - embed_gguf configured in ~/.ccllrun/config.json; otherwise the proxy
      returns 503
    - PyMuPDF in the venv: use ~/.ccllrun/venv/bin/python

The index is intentionally minimal JSON loaded in RAM to show the flow. For very
large corpora, use a real vector database.
"""
import hashlib
import json
import math
import sys
import urllib.request
from pathlib import Path

PROXY = "http://127.0.0.1:8765"
INDEX = Path.home() / ".ccllrun" / "rag_index.json"
# Keep chunks small because technical text is token-dense and each chunk must fit
# within the embedding server batch/context.
CHUNK_WORDS = 150
TOP_K = 5


# ---------- proxy calls ----------
def _post(path, payload):
    req = urllib.request.Request(
        PROXY + path,
        data=json.dumps(payload).encode(),
        headers={"content-type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code in (501, 503):
            sys.exit("Embeddings non disponibili: imposta embed_gguf in "
                     "~/.ccllrun/config.json e riavvia (ccllrun stop && ccllrun servers).")
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode()[:200]}")


def embed(texts):
    """Vectorize strings through /v1/embeddings."""
    data = _post("/v1/embeddings", {"model": "embed", "input": texts})
    return [row["embedding"] for row in data["data"]]


def ask_big(question, context):
    """Ask the big model to answer using the retrieved chunks."""
    data = _post("/v1/messages", {
        "model": "qwen-big",
        "max_tokens": 800,
        "messages": [{"role": "user", "content":
            "Rispondi alla domanda usando SOLO il contesto qui sotto. Se il "
            "contesto non basta, dillo.\n\n=== CONTESTO ===\n" + context +
            "\n\n=== DOMANDA ===\n" + question}],
    })
    return "".join(b.get("text", "") for b in data.get("content", []))


# OCR is opt-in through --ocr because it is slow. OCR_LANG defaults to ita+eng;
# if the language pack is missing, the code falls back to English.
USE_OCR = False
OCR_LANG = "ita+eng"


def _ocr_page(page):
    """Render one PDF page and run tesseract. OCR is best-effort."""
    import shutil, subprocess, tempfile
    if not shutil.which("tesseract"):
        return ""
    pix = page.get_pixmap(dpi=200)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        pix.save(f.name); img = f.name
    try:
        lang = OCR_LANG
        out = subprocess.run(["tesseract", img, "-", "-l", lang],
                             capture_output=True, text=True)
        if out.returncode != 0 and lang != "eng":
            out = subprocess.run(["tesseract", img, "-", "-l", "eng"],
                                 capture_output=True, text=True)
        return out.stdout if out.returncode == 0 else ""
    finally:
        import os as _os
        _os.unlink(img)


# ---------- utilities ----------
def pdf_to_chunks(pdf_path):
    import fitz  # PyMuPDF
    try:
        doc = fitz.open(pdf_path)
    except Exception:
        return  # PDF illeggibile/corrotto/placeholder: 0 chunk (gestito a monte)
    words = []
    for page in doc:
        words += page.get_text().split()
    if not words and USE_OCR:
        for page in doc:
            words += _ocr_page(page).split()
    for i in range(0, len(words), CHUNK_WORDS):
        chunk = " ".join(words[i:i + CHUNK_WORDS]).strip()
        if chunk:
            yield chunk


def zero_chunk_reason(pdf_path):
    """Explain why a PDF produced no chunks."""
    try:
        size = Path(pdf_path).stat().st_size
    except OSError:
        return "file non accessibile"
    if size < 1024:
        return f"file non scaricato in locale ({size} byte) — rendilo disponibile offline"
    return "nessun testo estraibile (PDF scansionato? servirebbe OCR)"


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb + 1e-9)


# ---------- dependency-free progress bar on stderr ----------
def progress(done, total, t0, label=""):
    """Render a single-line progress bar with percentage and ETA."""
    import time
    width = 28
    frac = done / total if total else 1.0
    filled = int(width * frac)
    bar = "█" * filled + "·" * (width - filled)
    elapsed = time.time() - t0
    eta = (elapsed / done * (total - done)) if done else 0
    mm, ss = divmod(int(eta), 60)
    label = (label[:30] + "…") if len(label) > 31 else label
    sys.stderr.write(f"\r[{bar}] {done}/{total} {frac*100:4.0f}%  ETA {mm:02d}:{ss:02d}  {label:<31}")
    sys.stderr.flush()
    if done >= total:
        sys.stderr.write("\n")


# ---------- commands ----------
def cmd_index(folder):
    import time
    folder = Path(folder).expanduser()
    pdfs = sorted(folder.rglob("*.pdf"))
    if not pdfs:
        sys.exit(f"nessun PDF in {folder}")
    print(f"[index] {len(pdfs)} PDF in {folder}")
    records = []
    seen = set()
    n_dup = n_zero = 0
    t0 = time.time()
    total = len(pdfs)
    for i, pdf in enumerate(pdfs, 1):
        progress(i - 1, total, t0, pdf.name)
        chunks = list(pdf_to_chunks(pdf))
        if not chunks:
            n_zero += 1
            print(f"\n  - {pdf.name}: 0 chunk ({zero_chunk_reason(pdf)})")
            continue
        digest = hashlib.sha1("\n".join(chunks).encode()).hexdigest()
        if digest in seen:
            n_dup += 1
            print(f"\n  - {pdf.name}: duplicato, saltato")
            continue
        seen.add(digest)
        try:
            vectors = embed(chunks)
        except RuntimeError as e:
            print(f"\n  - {pdf.name}: SALTATO ({e})")
            continue
        for c, v in zip(chunks, vectors):
            records.append({"file": str(pdf), "text": c, "vec": v})
        print(f"\n  - {pdf.name}: {len(chunks)} chunk indicizzati")
    progress(total, total, t0)
    INDEX.write_text(json.dumps(records))
    print(f"[index] {len(records)} chunk salvati in {INDEX} "
          f"(saltati: {n_dup} duplicati, {n_zero} senza testo)")


def cmd_query(question):
    if not INDEX.is_file():
        sys.exit("indice mancante: lancia prima `index <cartella>`")
    records = json.loads(INDEX.read_text())
    qvec = embed([question])[0]
    ranked = sorted(records, key=lambda r: cosine(qvec, r["vec"]), reverse=True)
    top = ranked[:TOP_K]
    print(f"[query] top {len(top)} chunk piu' pertinenti:")
    context_parts = []
    for r in top:
        print(f"  - {Path(r['file']).name}: {r['text'][:80]}...")
        context_parts.append(f"[{Path(r['file']).name}] {r['text']}")
    print("\n[query] risposta del modello big:\n")
    print(ask_big(question, "\n\n".join(context_parts)))


def main():
    global USE_OCR
    args = sys.argv[1:]
    if "--ocr" in args:
        USE_OCR = True
        args.remove("--ocr")
    if len(args) < 2 or args[0] not in ("index", "query"):
        sys.exit(__doc__)
    if args[0] == "index":
        cmd_index(args[1])
    else:
        cmd_query(" ".join(args[1:]))


if __name__ == "__main__":
    main()
