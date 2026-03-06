# ⛓ GRAINLINK – Setup Anleitung
## Synology DS716+ · Docker · Claude Desktop / Cursor

---

## 1. Synology vorbereiten

SSH aktivieren: **DSM → Systemsteuerung → Terminal & SNMP → SSH-Dienst aktivieren**

```bash
# SSH auf die NAS
ssh dein-user@NAS-IP

# Ordner anlegen
mkdir -p /volume1/docker/grainlink/{data,logs}
```

> 💡 Falls `docker compose` nur mit `sudo` funktioniert:
> ```bash
> sudo synogroup --add docker $USER
> exit  # neu einloggen danach
> ```

---

## 2. Dateien auf die NAS kopieren

```bash
# Von deinem PC aus
scp -r ./grainlink dein-user@NAS-IP:/volume1/docker/
```

---

## 3. Embedding-Modell herunterladen (einmalig)

> ⚠️ Dieser Schritt muss **vor** dem Docker-Build ausgeführt werden.
> Das Modell (~90 MB) wird lokal gespeichert und beim Build ins Image kopiert.
> So ist kein Internet-Zugriff zur Laufzeit nötig.

```bash
ssh dein-user@NAS-IP
cd /volume1/docker/grainlink
chmod +x download_model.sh
sudo bash download_model.sh
```

Erwartete Ausgabe:
```
⛓ GRAINLINK — Downloading embedding model...
→ Starting download container...
✅ Model downloaded successfully
✅ Model saved to: /volume1/docker/grainlink/model_cache
→ Now run: docker compose up -d --build
```

---

## 4. Docker Image bauen & starten

```bash
cd /volume1/docker/grainlink
sudo docker compose up -d --build
```

> ⏱️ Erster Build dauert ~5–10 Min (PyTorch CPU ~800 MB).
> Folge-Builds sind dank Cache in ~1 Min fertig.

Logs prüfen:
```bash
sudo docker logs grainlink -f
```

Erwartete Ausgabe (kein einziger HuggingFace HTTP-Request):
```
✅ Model loaded.
⛓ GRAINLINK starting — Every thought. Every agent. One link.
```

---

## 5. SSH-Key einrichten (für Claude Desktop)

Claude Desktop verbindet sich per SSH mit der NAS. Damit kein Passwort abgefragt wird:

```bash
# Auf deinem PC (nicht auf der NAS)
ssh-keygen -t ed25519 -f ~/.ssh/grainlink_key -N ""
ssh-copy-id -i ~/.ssh/grainlink_key dein-user@NAS-IP

# Test
ssh -i ~/.ssh/grainlink_key dein-user@NAS-IP "docker exec grainlink echo OK"
# → sollte "OK" ausgeben
```

---

## 6. Claude Desktop konfigurieren

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

**Claude Desktop neu starten** – unten links erscheint das 🔨 Hammer-Symbol wenn GRAINLINK verbunden ist.

---

## 7. Cursor konfigurieren

Globale Config: `~/.cursor/mcp.json`

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

---

## 8. Funktionstest

In Claude Desktop schreiben:

```
Merke dir: Ich bevorzuge TypeScript, arbeite an Projekt GRAINLINK
(Python MCP Server), läuft auf Synology DS716+.
```

Claude ruft automatisch `remember` auf. Beim nächsten Chat – auch in Cursor – ist dieser Kontext sofort verfügbar.

Erinnerungen prüfen:
```
Zeige mir alle gespeicherten Erinnerungen.
```

---

## 9. Verfügbare Tools

| Tool | Beschreibung |
|---|---|
| `remember` | Speichert eine Erinnerung mit Tags & Wichtigkeit (1–10) |
| `recall` | Semantische Suche über alle Erinnerungen |
| `set_fact` | Key-Value Fakt setzen (Präferenzen, Einstellungen) |
| `get_facts` | Alle Fakten abrufen |
| `get_context` | Fertiger System-Prompt-Block für ein bestimmtes Thema |
| `forget` | Erinnerung per ID löschen |
| `list_recent` | Letzte Erinnerungen anzeigen |

---

## 10. Tipps & Wartung

**Automatischer Kontext am Chat-Anfang:**
Füge deinem Claude System-Prompt hinzu:
```
Rufe zu Beginn jedes Gesprächs get_context mit dem aktuellen
Thema auf, um relevante Erinnerungen zu laden.
```

**Backup der Datenbank:**
```bash
# Einmalig via Synology Hyper Backup einrichten:
/volume1/docker/grainlink/data/memory.db
```

**Container-Status prüfen:**
```bash
sudo docker stats grainlink
sudo docker logs grainlink --tail 50
```

**Container neu starten:**
```bash
sudo docker compose -f /volume1/docker/grainlink/docker-compose.yml restart
```

**Troubleshooting – MCP nicht verbunden:**
```bash
# SSH-Verbindung direkt testen
ssh -i ~/.ssh/grainlink_key dein-user@NAS-IP \
  "echo '{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/list\",\"params\":{}}' | \
   docker exec -i grainlink python /app/server.py"
# → sollte JSON mit Tool-Liste zurückgeben
```
