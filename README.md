# ESPHome JSD Solar J6500HC

Configuration ESPHome et outils de debug pour surveiller un onduleur JSD Solar J6500HC via RS232/TTL.

> Version préparée pour GitHub : secrets, captures brutes, sauvegardes et fichiers de travail locaux sont exclus.

Objectif : produire une configuration ESPHome de production et un outillage debug pour un JSD Solar J6500HC connecté en RS232 passif à un ESP32-C3 Supermini.

## Documentation

- `docs/TECHNICAL_DOCUMENTATION.md` : documentation technique structurée du projet.
- `docs/ARTICLE_DOSSIER.md` : dossier narratif pour préparer un futur article.
- `docs/PASSIVE_CAPTURE_REPORT.md` : rapport de capture passive.
- `docs/ACTIVE_PROBE_REPORT.md` : rapport du probe actif read-only.
- `docs/EXTERNAL_YAML_ANALYSIS.md` : analyse du fichier externe `esphome-j6500hc-loggger-mod.yaml`.
- `docs/GATEWAY_PARALLEL_DEBUG.md` : câblage et règles pour garder la passerelle IP/RS232 en parallèle.
- `docs/DEBUG_STREAM_GATEWAY.md` : firmware ESPHome dédié passerelle TCP brute sur le port 6666.
- `docs/WIRING_DIAGRAM.md` : schéma de branchement USB-A RS232, MAX3232 et ESP32-C3 Supermini.
- `docs/ALARM_CODES_MAPPING.md` : corrélation provisoire des alarmes 68/69 avec la capture alarme.
- `docs/QUESTIONS.md` : questions restantes à trancher.

## Fichiers

- `original.yaml` : fichier fourni, référence non modifiée.
- `backup/original.yaml` : sauvegarde de référence.
- `configs/production.yaml` : copie de production conservatrice, RX-only, mêmes entités.
- `configs/debug.yaml` : variante ESPHome avec logs `DEBUG`, RX-only et blocs hex de diagnostic.
- `configs/debug-stream-gateway.yaml` : firmware alternatif TX/RX exposant l’UART en TCP brut sur `192.168.x.x:6666`.
- `scripts/passive_capture.py` : capture passive via passerelle IP/RS232 `192.168.x.x:6666`, n’envoie aucune requête Modbus.
- `scripts/active_read_probe.py` : probe actif read-only, envoie des requêtes Modbus FC03/FC04, aucune écriture. À lancer seulement après accord.
- `scripts/analyze_capture.py` : résumé des captures JSONL.

## Commandes utiles

Capture passive, sans émission série :

```bash
cd /root/.hermes/projects/esphome-jsdsolar-j6500hc/scripts
python3 passive_capture.py --host 192.168.x.x --port 6666 --seconds 120 --out ../captures/passive.jsonl
python3 analyze_capture.py ../captures/passive.jsonl
```

Probe actif read-only, seulement après validation :

```bash
cd /root/.hermes/projects/esphome-jsdsolar-j6500hc/scripts
python3 active_read_probe.py --host 192.168.x.x --port 6666 --function 3 --out ../captures/fc03_probe.jsonl
python3 active_read_probe.py --host 192.168.x.x --port 6666 --function 4 --out ../captures/fc04_probe.jsonl
```
