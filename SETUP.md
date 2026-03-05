# GRAINLINK – Setup Anleitung
## Synology DS716+ + Claude Desktop

---

## 1. Synology vorbereiten

```bash
# SSH auf die NAS aktivieren (DSM → Systemsteuerung → Terminal & SNMP)
ssh dein-user@NAS-IP

# Ordner anlegen
mkdir -p /volume1/docker/grainlink/data
mkdir -p /volume1/docker/grainlink/logs
```

---

## 2. Docker Image bauen & starten

```bash
# Dateien auf die NAS kopieren (von deinem PC)
scp -r ./mcp-memory dein-user@NAS-IP:/volume1/docker/

# Auf der NAS:
cd /volume1/docker/mcp-memory
docker compose up -d --build

# Logs prüfen
docker logs grainlink -f
```

> ⚠️ Erster Build dauert ~10-20 Min (PyTorch CPU download ~800MB)

---

## 3. Claude Desktop konfigurieren

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

> 💡 Tipp: SSH-Key einrichten damit kein Passwort gefragt wird:
> `ssh-copy-id dein-user@NAS-IP`

---

## 4. Cursor konfigurieren

In `.cursor/mcp.json` (Projekt-Root oder global):

```json
{
  "mcpServers": {
    "grainlink": {
      "command": "ssh",
      "args": [
        "dein-user@NAS-IP",
        "docker exec -i grainlink python /app/server.py"
      ]
    }
  }
}
```

---

## 5. Funktionstest

In Claude Desktop einfach schreiben:

```
Merke dir: Ich bevorzuge TypeScript, arbeite an Projekt Phoenix 
(Node.js Monorepo), deploye auf Hetzner VPS.
```

Claude ruft automatisch das `remember`-Tool auf. Beim nächsten 
Chat – auch in Cursor – ist dieser Kontext sofort verfügbar.

---

## 6. Verfügbare Tools

| Tool | Beschreibung |
|------|-------------|
| `remember` | Speichert eine Erinnerung mit Tags & Wichtigkeit |
| `recall` | Semantische Suche über alle Erinnerungen |
| `set_fact` | Key-Value Fakt setzen (Präferenzen etc.) |
| `get_facts` | Alle Fakten abrufen |
| `get_context` | Fertiger System-Prompt für ein Thema |
| `forget` | Erinnerung löschen |
| `list_recent` | Letzte Erinnerungen anzeigen |

---

## 7. Tipps

**Automatischer Kontext am Anfang jedes Chats:**
Füge deinem Claude System-Prompt hinzu:
```
Rufe zu Beginn jedes Gesprächs `get_context` mit dem aktuellen 
Thema auf, um relevante Erinnerungen zu laden.
```

**Backup der Datenbank:**
```bash
# Synology Hyper Backup einrichten für:
/volume1/docker/grainlink/data/memory.db
```

**Speicherverbrauch prüfen:**
```bash
docker stats grainlink
```
