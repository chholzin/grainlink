# ⛓ GRAINLINK — MCP Memory Server

> *Every thought. Every agent. One link.*

> **[Deutsch](#deutsch) | [English](#english)**

---

<a name="deutsch"></a>
## 🇩🇪 Deutsch

### Was ist das?

Der **GRAINLINK** ist ein zentrales, persistentes Gedächtnis-System für alle deine KI-Agenten. Egal ob du mit Claude, GPT-4, Cursor oder einem anderen Agenten arbeitest – alle teilen sich dieselbe Wissensbasis. Du musst deinen Kontext nie mehr neu promten, wenn du zwischen Agenten wechselst.

Der Server läuft als Docker-Container auf deinem Synology NAS, vollständig lokal. Kein Datei verlässt dein Heimnetz.

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Claude    │   │  Cursor AI  │   │   GPT-4o    │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       └────────────┬────┘─────────────────┘
                    │  MCP / REST
          ┌─────────▼──────────┐
          │       GRAINLINK        │  ← läuft auf Synology NAS
          │  (MCP Memory Server)   │
          └─────────┬──────────┘
                    │
          ┌─────────▼──────────┐
          │  SQLite + Embeddings│  ← vollständig lokal
          │  (all-MiniLM-L6-v2) │
          └────────────────────┘
```

### Features

- **Semantische Suche** — findet relevante Erinnerungen anhand von Bedeutung, nicht nur Keywords
- **Vollständig lokal** — kein Cloud-Dienst, keine externe API, volle Datenkontrolle
- **Agent-übergreifend** — ein Gedächtnis für Claude, Cursor, GPT und jeden anderen Agenten
- **Persistent** — Erinnerungen überleben Neustarts und bleiben dauerhaft erhalten
- **Leichtgewichtig** — läuft komfortabel auf einem Synology NAS mit 8 GB RAM
- **Docker-ready** — ein Befehl zum Starten, kein kompliziertes Setup

### Voraussetzungen

| Komponente | Minimum | Empfohlen |
|---|---|---|
| RAM | 4 GB | 8 GB (wie DS716+) |
| CPU | Intel x86_64 | Intel Celeron N3150+ |
| DSM | 6.2+ | 7.x |
| Docker | Package Center | Container Manager |
| Python | — | im Docker enthalten |

### Schnellstart

```bash
# 1. SSH auf die NAS
ssh dein-user@NAS-IP

# 2. Ordner anlegen
mkdir -p /volume1/docker/grainlink/{data,logs}

# 3. Dateien auf die NAS kopieren (von deinem PC)
scp -r ./mcp-memory dein-user@NAS-IP:/volume1/docker/

# 4. Container bauen und starten
cd /volume1/docker/mcp-memory
docker compose up -d --build

# 5. Logs prüfen
docker logs grainlink -f
```

> ⏱️ Der erste Build dauert ~15–20 Minuten (PyTorch CPU ~800 MB Download).  
> Danach startet der Container in wenigen Sekunden.

### Claude Desktop einrichten

Datei öffnen:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "grainlink": {
      "command": "ssh",
      "args": [
        "-i", "/Users/DEIN-USER/.ssh/id_rsa",
        "dein-user@NAS-IP",
        "docker exec -i grainlink python /app/server.py"
      ]
    }
  }
}
```

> 💡 SSH-Key einrichten für passwortlosen Zugriff:  
> `ssh-copy-id dein-user@NAS-IP`

### Verfügbare Tools

| Tool | Beschreibung |
|---|---|
| `remember` | Speichert eine Erinnerung mit optionalen Tags und Wichtigkeit (1–10) |
| `recall` | Semantische Suche – findet relevante Erinnerungen zu einem Thema |
| `set_fact` | Speichert einen stabilen Fakt als Key-Value Paar |
| `get_facts` | Gibt alle gespeicherten Fakten zurück |
| `get_context` | Liefert einen fertigen System-Prompt-Block für ein bestimmtes Thema |
| `forget` | Löscht eine Erinnerung anhand ihrer ID |
| `list_recent` | Zeigt die zuletzt gespeicherten Erinnerungen |

### Beispiel-Nutzung

In Claude Desktop einfach schreiben:

```
Merke dir: Ich arbeite an Projekt Phoenix, einem Node.js Monorepo.
Wir deployen auf Hetzner. Ich bevorzuge TypeScript und kurze Antworten.
```

Claude ruft `remember` automatisch auf. Beim nächsten Chat – auch in Cursor – ist dieser Kontext sofort verfügbar.

Oder explizit Kontext laden:

```
Lade meinen Kontext zum Thema "Deployment".
```

Claude ruft `get_context` auf und bekommt einen fertigen Block mit allen relevanten Fakten und Erinnerungen.

### Datei-Übersicht

```
mcp-memory/
├── server.py           # MCP Server (Haupt-Logik)
├── Dockerfile          # Container-Definition
├── docker-compose.yml  # Synology-optimiertes Deployment
├── requirements.txt    # Python-Abhängigkeiten
├── SETUP.md            # Detaillierte Setup-Anleitung
└── README.md           # Diese Datei
```

### Backup

Die gesamte Datenbank liegt in einer einzigen Datei:
```
/volume1/docker/grainlink/data/memory.db
```
Diese Datei in Synology Hyper Backup einbinden – fertig.

---

<a name="english"></a>
## 🇬🇧 English

### What is this?

**GRAINLINK** is a central, persistent memory system for all your AI agents. Whether you're working with Claude, GPT-4, Cursor, or any other agent — they all share the same knowledge base. You never have to re-prompt your context again when switching between agents.

The server runs as a Docker container on your Synology NAS, completely locally. No data ever leaves your home network.

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Claude    │   │  Cursor AI  │   │   GPT-4o    │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       └────────────┬────┘─────────────────┘
                    │  MCP / REST
          ┌─────────▼──────────┐
          │       GRAINLINK        │  ← runs on Synology NAS
          │  (MCP Memory Server)   │
          └─────────┬──────────┘
                    │
          ┌─────────▼──────────┐
          │  SQLite + Embeddings│  ← fully local
          │  (all-MiniLM-L6-v2) │
          └────────────────────┘
```

### Features

- **Semantic search** — finds relevant memories by meaning, not just keywords
- **Fully local** — no cloud service, no external API, complete data control
- **Cross-agent** — one shared memory for Claude, Cursor, GPT, and any other agent
- **Persistent** — memories survive restarts and are retained indefinitely
- **Lightweight** — runs comfortably on a Synology NAS with 8 GB RAM
- **Docker-ready** — one command to start, no complex setup required

### Requirements

| Component | Minimum | Recommended |
|---|---|---|
| RAM | 4 GB | 8 GB (like DS716+) |
| CPU | Intel x86_64 | Intel Celeron N3150+ |
| DSM | 6.2+ | 7.x |
| Docker | Package Center | Container Manager |
| Python | — | included in Docker |

### Quick Start

```bash
# 1. SSH into your NAS
ssh your-user@NAS-IP

# 2. Create directories
mkdir -p /volume1/docker/grainlink/{data,logs}

# 3. Copy files to the NAS (from your PC)
scp -r ./mcp-memory your-user@NAS-IP:/volume1/docker/

# 4. Build and start the container
cd /volume1/docker/mcp-memory
docker compose up -d --build

# 5. Check logs
docker logs grainlink -f
```

> ⏱️ The first build takes ~15–20 minutes (PyTorch CPU ~800 MB download).  
> After that, the container starts in seconds.

### Claude Desktop Setup

Open the config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "grainlink": {
      "command": "ssh",
      "args": [
        "-i", "/Users/YOUR-USER/.ssh/id_rsa",
        "your-user@NAS-IP",
        "docker exec -i grainlink python /app/server.py"
      ]
    }
  }
}
```

> 💡 Set up an SSH key for passwordless access:  
> `ssh-copy-id your-user@NAS-IP`

### Available Tools

| Tool | Description |
|---|---|
| `remember` | Stores a memory with optional tags and importance (1–10) |
| `recall` | Semantic search — finds relevant memories on a topic |
| `set_fact` | Stores a stable fact as a key-value pair |
| `get_facts` | Returns all stored facts |
| `get_context` | Returns a ready-made system prompt block for a given topic |
| `forget` | Deletes a memory by its ID |
| `list_recent` | Shows the most recently stored memories |

### Usage Example

Simply write in Claude Desktop:

```
Remember: I'm working on Project Phoenix, a Node.js monorepo.
We deploy on Hetzner. I prefer TypeScript and concise answers.
```

Claude automatically calls `remember`. In the next chat — even in Cursor — this context is immediately available.

Or explicitly load context:

```
Load my context on the topic "deployment".
```

Claude calls `get_context` and receives a ready-made block with all relevant facts and memories.

### File Overview

```
mcp-memory/
├── server.py           # MCP Server (core logic)
├── Dockerfile          # Container definition
├── docker-compose.yml  # Synology-optimised deployment
├── requirements.txt    # Python dependencies
├── SETUP.md            # Detailed setup guide
└── README.md           # This file
```

### Backup

The entire database lives in a single file:
```
/volume1/docker/grainlink/data/memory.db
```
Just add this file to Synology Hyper Backup — done.

---

*Built for Synology DS716+ · Intel Celeron N3150 · 8 GB RAM · Fully local · No cloud required*
