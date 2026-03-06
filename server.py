#!/usr/bin/env python3
"""
GRAINLINK — MCP Memory Server
Every thought. Every agent. One link.
Runs on Synology NAS, fully local, no external API needed.
"""

import asyncio
import json
import sqlite3
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# ── Config ────────────────────────────────────────────────────────────────────
DB_PATH   = Path(os.getenv("DB_PATH",   "/data/memory.db"))
LOG_PATH  = Path(os.getenv("LOG_PATH",  "/logs/memory.log"))
MODEL_NAME = os.getenv("EMBED_MODEL",  "all-MiniLM-L6-v2")  # ~80MB, fast on Celeron
TOP_K      = int(os.getenv("TOP_K",    "5"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler()
    ]
)
log = logging.getLogger("grainlink")

# ── Database ──────────────────────────────────────────────────────────────────
def init_db(conn: sqlite3.Connection):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            content     TEXT    NOT NULL,
            summary     TEXT,
            tags        TEXT    DEFAULT '[]',
            source      TEXT    DEFAULT 'user',
            importance  INTEGER DEFAULT 5,
            embedding   BLOB,
            created_at  TEXT    NOT NULL,
            updated_at  TEXT    NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS facts (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            key         TEXT    UNIQUE NOT NULL,
            value       TEXT    NOT NULL,
            updated_at  TEXT    NOT NULL
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tags ON memories(tags)")
    conn.commit()
    log.info("Database initialised at %s", DB_PATH)

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── Embedding (ONNX Runtime — no PyTorch, ~150MB image) ──────────────────────
import json as _json
from tokenizers import Tokenizer
import onnxruntime as ort

_tokenizer: Tokenizer | None = None
_session:   ort.InferenceSession | None = None

def _load_model():
    global _tokenizer, _session
    model_dir = Path(os.getenv("SENTENCE_TRANSFORMERS_HOME", "/app/model_cache")) / MODEL_NAME
    _tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
    _tokenizer.enable_padding(pad_id=0, pad_token="[PAD]", length=128)
    _tokenizer.enable_truncation(max_length=128)
    _session = ort.InferenceSession(
        str(model_dir / "onnx" / "model.onnx"),
        providers=["CPUExecutionProvider"]
    )
    log.info("✅ ONNX model loaded from %s", model_dir)

def _mean_pool(token_embeddings: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
    mask = attention_mask[..., np.newaxis].astype(float)
    summed = (token_embeddings * mask).sum(axis=1)
    counts = mask.sum(axis=1).clip(min=1e-9)
    return summed / counts

def embed(text: str) -> bytes:
    assert _session is not None, "Model not loaded"
    enc = _tokenizer.encode(text)
    input_ids      = np.array([enc.ids],               dtype=np.int64)
    attention_mask = np.array([enc.attention_mask],     dtype=np.int64)
    token_type_ids = np.zeros_like(input_ids)
    outputs = _session.run(None, {
        "input_ids":      input_ids,
        "attention_mask": attention_mask,
        "token_type_ids": token_type_ids,
    })
    pooled = _mean_pool(outputs[0], attention_mask)
    norm   = np.linalg.norm(pooled, axis=1, keepdims=True)
    vec    = (pooled / norm.clip(min=1e-9)).astype(np.float32)
    return vec[0].tobytes()

def cosine_similarity(a: bytes, b: bytes) -> float:
    va = np.frombuffer(a, dtype=np.float32)
    vb = np.frombuffer(b, dtype=np.float32)
    return float(np.dot(va, vb))

# ── MCP Server ────────────────────────────────────────────────────────────────
app = Server("grainlink")

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="remember",
            description=(
                "Speichert eine wichtige Information dauerhaft im gemeinsamen Gedächtnis. "
                "Nutze dies für Entscheidungen, Präferenzen, Projekt-Details, Learnings oder "
                "alles was beim nächsten Gespräch – auch mit einem anderen KI-Agenten – "
                "noch relevant sein könnte."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "content":    {"type": "string", "description": "Was soll gemerkt werden?"},
                    "tags":       {"type": "array",  "items": {"type": "string"},
                                   "description": "Themen-Tags z.B. ['projekt-x', 'architektur']"},
                    "importance": {"type": "integer", "minimum": 1, "maximum": 10,
                                   "description": "Wichtigkeit 1-10 (Standard: 5)"},
                    "source":     {"type": "string", "description": "Welcher Agent speichert das?"}
                },
                "required": ["content"]
            }
        ),
        types.Tool(
            name="recall",
            description=(
                "Sucht semantisch ähnliche Erinnerungen zum gegebenen Thema/Frage. "
                "Nutze dies am Anfang jeder Konversation oder wenn du Kontext zu einem Thema brauchst."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query":      {"type": "string", "description": "Was suchst du?"},
                    "limit":      {"type": "integer", "default": 5,
                                   "description": "Maximale Anzahl Ergebnisse"},
                    "tags":       {"type": "array", "items": {"type": "string"},
                                   "description": "Optional: nur Erinnerungen mit diesen Tags"}
                },
                "required": ["query"]
            }
        ),
        types.Tool(
            name="set_fact",
            description=(
                "Speichert einen Fakt als Key-Value Paar (überschreibt bestehenden Wert). "
                "Ideal für stabile Infos: Präferenzen, Namen, Einstellungen, Technologie-Stack."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "key":   {"type": "string", "description": "z.B. 'preferred_language'"},
                    "value": {"type": "string", "description": "z.B. 'TypeScript'"}
                },
                "required": ["key", "value"]
            }
        ),
        types.Tool(
            name="get_facts",
            description="Gibt alle gespeicherten Fakten zurück (Key-Value Paare).",
            inputSchema={"type": "object", "properties": {}}
        ),
        types.Tool(
            name="get_context",
            description=(
                "Gibt einen fertigen Kontext-Block zurück der als System-Prompt verwendet werden kann. "
                "Enthält die wichtigsten Fakten + relevante Erinnerungen zum gegebenen Thema."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "Aktuelles Gesprächsthema"}
                },
                "required": ["topic"]
            }
        ),
        types.Tool(
            name="forget",
            description="Löscht eine Erinnerung anhand ihrer ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "memory_id": {"type": "integer", "description": "ID aus recall-Ergebnissen"}
                },
                "required": ["memory_id"]
            }
        ),
        types.Tool(
            name="list_recent",
            description="Listet die zuletzt gespeicherten Erinnerungen auf.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10}
                }
            }
        ),
    ]

# ── Tool Handlers ─────────────────────────────────────────────────────────────
@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    conn = get_conn()
    now  = datetime.utcnow().isoformat()

    try:
        if name == "remember":
            content    = arguments["content"]
            tags       = json.dumps(arguments.get("tags", []))
            importance = arguments.get("importance", 5)
            source     = arguments.get("source", "agent")
            vec        = embed(content)

            cur = conn.execute(
                "INSERT INTO memories (content, tags, importance, source, embedding, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (content, tags, importance, source, vec, now, now)
            )
            conn.commit()
            log.info("Stored memory #%d: %s", cur.lastrowid, content[:60])
            return [types.TextContent(type="text",
                text=f"✅ Gespeichert als Erinnerung #{cur.lastrowid}")]

        elif name == "recall":
            query  = arguments["query"]
            limit  = arguments.get("limit", TOP_K)
            f_tags = arguments.get("tags", [])
            q_vec  = embed(query)

            rows = conn.execute(
                "SELECT id, content, tags, importance, source, created_at, embedding FROM memories"
            ).fetchall()

            scored = []
            for r in rows:
                if f_tags:
                    r_tags = json.loads(r["tags"])
                    if not any(t in r_tags for t in f_tags):
                        continue
                score = cosine_similarity(q_vec, r["embedding"])
                scored.append((score, r))

            scored.sort(key=lambda x: x[0], reverse=True)
            top = scored[:limit]

            if not top:
                return [types.TextContent(type="text", text="Keine relevanten Erinnerungen gefunden.")]

            lines = [f"🧠 **{len(top)} Erinnerungen gefunden:**\n"]
            for score, r in top:
                tags_str = ", ".join(json.loads(r["tags"])) or "–"
                lines.append(
                    f"**#{r['id']}** (Relevanz: {score:.0%} | Wichtigkeit: {r['importance']}/10)\n"
                    f"{r['content']}\n"
                    f"_Tags: {tags_str} | Quelle: {r['source']} | {r['created_at'][:10]}_\n"
                )
            return [types.TextContent(type="text", text="\n".join(lines))]

        elif name == "set_fact":
            key   = arguments["key"]
            value = arguments["value"]
            conn.execute(
                "INSERT INTO facts (key, value, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
                (key, value, now)
            )
            conn.commit()
            log.info("Set fact: %s = %s", key, value)
            return [types.TextContent(type="text", text=f"✅ Fakt gesetzt: **{key}** = {value}")]

        elif name == "get_facts":
            rows = conn.execute("SELECT key, value, updated_at FROM facts ORDER BY key").fetchall()
            if not rows:
                return [types.TextContent(type="text", text="Noch keine Fakten gespeichert.")]
            lines = ["📋 **Gespeicherte Fakten:**\n"]
            for r in rows:
                lines.append(f"• **{r['key']}**: {r['value']}")
            return [types.TextContent(type="text", text="\n".join(lines))]

        elif name == "get_context":
            topic = arguments["topic"]

            # Facts
            facts = conn.execute("SELECT key, value FROM facts ORDER BY key").fetchall()
            facts_block = "\n".join(f"- {r['key']}: {r['value']}" for r in facts) or "Keine."

            # Relevant memories
            q_vec = embed(topic)
            rows  = conn.execute(
                "SELECT id, content, importance, embedding FROM memories ORDER BY importance DESC"
            ).fetchall()
            scored = sorted(rows, key=lambda r: cosine_similarity(q_vec, r["embedding"]), reverse=True)
            top5   = [r["content"] for r in scored[:5]]
            mem_block = "\n".join(f"- {c}" for c in top5) or "Keine."

            context = (
                f"## Persönlicher Kontext (GRAINLINK)\n\n"
                f"### Bekannte Fakten\n{facts_block}\n\n"
                f"### Relevante Erinnerungen zum Thema '{topic}'\n{mem_block}\n\n"
                f"_Dieser Kontext wurde automatisch aus dem gemeinsamen Gedächtnis geladen._"
            )
            return [types.TextContent(type="text", text=context)]

        elif name == "forget":
            mid = arguments["memory_id"]
            conn.execute("DELETE FROM memories WHERE id = ?", (mid,))
            conn.commit()
            return [types.TextContent(type="text", text=f"🗑️ Erinnerung #{mid} gelöscht.")]

        elif name == "list_recent":
            limit = arguments.get("limit", 10)
            rows  = conn.execute(
                "SELECT id, content, tags, importance, source, created_at FROM memories "
                "ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            if not rows:
                return [types.TextContent(type="text", text="Noch keine Erinnerungen gespeichert.")]
            lines = [f"📜 **Letzte {len(rows)} Erinnerungen:**\n"]
            for r in rows:
                tags_str = ", ".join(json.loads(r["tags"])) or "–"
                lines.append(f"**#{r['id']}** [{r['created_at'][:10]}] {r['content'][:80]}…\n_Tags: {tags_str}_\n")
            return [types.TextContent(type="text", text="\n".join(lines))]

        else:
            return [types.TextContent(type="text", text=f"Unbekanntes Tool: {name}")]

    finally:
        conn.close()

# ── Entrypoint ────────────────────────────────────────────────────────────────
async def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    init_db(conn)
    conn.close()
    # Load ONNX model BEFORE opening stdio — fast start, no HuggingFace requests
    log.info("Loading ONNX embedding model '%s' ...", MODEL_NAME)
    _load_model()

    log.info("⛓ GRAINLINK starting — Every thought. Every agent. One link.")
    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
