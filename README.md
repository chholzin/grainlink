# ⛓ GRAINLINK — MCP Memory Server

> *Every thought. Every agent. One link.*

> **[Deutsch](#deutsch) | [English](#english)**

---

<a name="deutsch"></a>
## 🇩🇪 Deutsch

### Was ist das?

**GRAINLINK** ist ein zentrales, persistentes Gedächtnis-System für alle deine KI-Agenten. Egal ob du mit Claude, GPT-4, Cursor oder einem anderen Agenten arbeitest – alle teilen sich dieselbe Wissensbasis. Du musst deinen Kontext nie mehr neu promten, wenn du zwischen Agenten wechselst.

Der Server läuft als Docker-Container auf deinem Synology NAS, vollständig lokal. Keine Daten verlassen dein Heimnetz. Inspiriert von der Gedächtnis-Technologie "Grain" aus Black Mirror.

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Claude    │   │  Cursor AI  │   │   GPT-4o    │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       └────────────┬────┘─────────────────┘
                    │  MCP (stdio über SSH)
          ┌─────────▼──────────────┐
          │       GRAINLINK        │  ← Synology NAS
          │   MCP Memory Server    │
          └─────────┬──────────────┘
                    │
          ┌─────────▼──────────────┐
          │  SQLite + Embeddings   │  ← vollständig lokal
          │  (all-MiniLM-L6-v2)   │     kein Internet nötig
          └────────────────────────┘
```

### Features

- **Semantische Suche** — findet relevante Erinnerungen anhand von Bedeutung, nicht nur Keywords
- **Vollständig offline** — Modell ist ins Docker-Image gebacken, kein Internet zur Laufzeit
- **Agent-übergreifend** — ein Gedächtnis für Claude, Cursor, GPT und jeden anderen Agenten
- **Persistent** — Erinnerungen überleben Neustarts und bleiben dauerhaft erhalten
- **Leichtgewichtig** — läuft komfortabel auf einem Synology NAS mit 8 GB RAM
- **Docker-ready** — reproduzierbares Setup, einfache Updates

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
# 1. Dateien auf die NAS kopieren
scp -r ./grainlink dein-user@NAS-IP:/volume1/docker/

# 2. SSH auf die NAS
ssh dein-user@NAS-IP
cd /volume1/docker/grainlink

# 3. Ordner anlegen
mkdir -p data logs

# 4. Modell herunterladen (einmalig, ~90 MB)
chmod +x download_model.sh
sudo bash download_model.sh

# 5. Container bauen und starten
sudo docker compose up -d --build

# 6. Logs prüfen
sudo docker logs grainlink -f
```

Erwartete Log-Ausgabe (ohne HTTP-Requests):
```
✅ Model loaded.
⛓ GRAINLINK starting — Every thought. Every agent. One link.
```

> Detaillierte Anleitung inkl. SSH-Key Setup und Troubleshooting: **SETUP.md**

### Claude Desktop einrichten

Config-Datei öffnen:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "grainlink": {
      "command": "ssh",
      "args": [
        "-i", "/Users/DEIN-USER/.ssh/grainlink_key",
        "-o", "StrictHostKeyChecking=no",
        "dein-user@NAS-IP",
        "docker exec -i grainlink python /app/server.py"
      ]
    }
  }
}
```

Nach dem Neustart von Claude Desktop erscheint unten links das 🔨 Symbol – GRAINLINK ist verbunden.

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

In Claude Desktop schreiben:

```
Merke dir: Ich arbeite an Projekt GRAINLINK, einem Python MCP Server.
Er läuft auf einer Synology DS716+ mit 8GB RAM. Ich bevorzuge kurze Antworten.
```

Claude ruft `remember` automatisch auf. Beim nächsten Chat – auch in Cursor – ist dieser Kontext sofort verfügbar.

Oder explizit Kontext laden:

```
Lade meinen Kontext zum Thema "NAS Setup".
```

### Datei-Übersicht

```
grainlink/
├── server.py            # MCP Server (Haupt-Logik)
├── Dockerfile           # Container-Definition
├── docker-compose.yml   # Synology-optimiertes Deployment
├── requirements.txt     # Python-Abhängigkeiten
├── download_model.sh    # Modell vorab herunterladen (einmalig)
├── .github/
│   └── workflows/
│       ├── ci.yml       # CI: Lint & Docker Build Test
│       └── release.yml  # Release: Push zu GHCR
├── .gitignore
├── SETUP.md             # Detaillierte Setup-Anleitung
└── README.md            # Diese Datei
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

The server runs as a Docker container on your Synology NAS, completely locally. No data ever leaves your home network. Inspired by the "Grain" memory implant from Black Mirror.

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Claude    │   │  Cursor AI  │   │   GPT-4o    │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                 │                 │
       └────────────┬────┘─────────────────┘
                    │  MCP (stdio over SSH)
          ┌─────────▼──────────────┐
          │       GRAINLINK        │  ← Synology NAS
          │   MCP Memory Server    │
          └─────────┬──────────────┘
                    │
          ┌─────────▼──────────────┐
          │  SQLite + Embeddings   │  ← fully local
          │  (all-MiniLM-L6-v2)   │     no internet needed
          └────────────────────────┘
```

### Features

- **Semantic search** — finds relevant memories by meaning, not just keywords
- **Fully offline** — model is baked into the Docker image, no internet at runtime
- **Cross-agent** — one shared memory for Claude, Cursor, GPT, and any other agent
- **Persistent** — memories survive restarts and are retained indefinitely
- **Lightweight** — runs comfortably on a Synology NAS with 8 GB RAM
- **Docker-ready** — reproducible setup, easy updates

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
# 1. Copy files to your NAS
scp -r ./grainlink your-user@NAS-IP:/volume1/docker/

# 2. SSH into your NAS
ssh your-user@NAS-IP
cd /volume1/docker/grainlink

# 3. Create directories
mkdir -p data logs

# 4. Download the embedding model (once, ~90 MB)
chmod +x download_model.sh
sudo bash download_model.sh

# 5. Build and start the container
sudo docker compose up -d --build

# 6. Check logs
sudo docker logs grainlink -f
```

Expected log output (no HTTP requests):
```
✅ Model loaded.
⛓ GRAINLINK starting — Every thought. Every agent. One link.
```

> For detailed instructions including SSH key setup and troubleshooting: **SETUP.md**

### Claude Desktop Setup

Open the config file:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "grainlink": {
      "command": "ssh",
      "args": [
        "-i", "/Users/YOUR-USER/.ssh/grainlink_key",
        "-o", "StrictHostKeyChecking=no",
        "your-user@NAS-IP",
        "docker exec -i grainlink python /app/server.py"
      ]
    }
  }
}
```

After restarting Claude Desktop, the 🔨 hammer icon appears in the bottom left — GRAINLINK is connected.

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

Write in Claude Desktop:

```
Remember: I'm working on GRAINLINK, a Python MCP Server.
It runs on a Synology DS716+ with 8GB RAM. I prefer concise answers.
```

Claude automatically calls `remember`. In the next chat — even in Cursor — this context is immediately available.

Or explicitly load context:

```
Load my context on the topic "NAS setup".
```

### File Overview

```
grainlink/
├── server.py            # MCP Server (core logic)
├── Dockerfile           # Container definition
├── docker-compose.yml   # Synology-optimised deployment
├── requirements.txt     # Python dependencies
├── download_model.sh    # One-time model download script
├── .github/
│   └── workflows/
│       ├── ci.yml       # CI: Lint & Docker build test
│       └── release.yml  # Release: push to GHCR
├── .gitignore
├── SETUP.md             # Detailed setup guide
└── README.md            # This file
```

### Backup

The entire database lives in a single file:
```
/volume1/docker/grainlink/data/memory.db
```
Add this file to Synology Hyper Backup — done.

---

*Built for Synology DS716+ · Intel Celeron N3150 · 8 GB RAM · Fully offline · No cloud required · Inspired by Black Mirror's "Grain"*
