# Documentation technique — ESPHome JSD Solar J6500HC

## Vue d’ensemble

Ce projet documente une intégration ESPHome pour surveiller un onduleur **JSD Solar J6500HC-48** depuis **Home Assistant**.

Le système repose sur une liaison **RS232 passive** : l’ESP32-C3 écoute le flux série émis par l’onduleur, décode les trames reçues et publie les mesures dans Home Assistant.

## Objectifs

- Conserver une configuration ESPHome de production stable.
- Ajouter une configuration debug pour analyser les valeurs incohérentes.
- Documenter les choix techniques pour un futur article.
- Identifier progressivement les champs encore inconnus : températures, mode GPB/PBG/PGB/MKS, paramètres de configuration.
- Éviter toute écriture Modbus vers l’onduleur tant que le protocole n’est pas parfaitement identifié.

## Matériel

| Élément | Détail |
|---|---|
| Onduleur | JSD Solar J6500HC-48 |
| Microcontrôleur | ESP32-C3 Supermini |
| Liaison | RS232 via port USB-A de l’onduleur |
| Adaptation niveau | Convertisseur RS232/TTL, type MAX3232 |
| GPIO ESPHome | RX sur GPIO20 |
| Home automation | Home Assistant |
| Debug temporaire | Passerelle IP/RS232 `192.168.x.x:6666` ou firmware `debug-stream-gateway.yaml` |

## Avertissement câblage

Le port USB-A de l’onduleur ne doit pas être traité comme un port USB standard côté ESP32. Dans ce projet, il transporte du RS232. Les niveaux RS232 ne sont pas compatibles directement avec les GPIO de l’ESP32.

Utiliser un convertisseur RS232/TTL adapté.

## Passerelle IP/RS232 en parallèle

La passerelle IP/RS232 `192.168.x.x:6666` peut rester branchée pour le debug externe, à condition de l’utiliser en **écoute passive RX-only**.

Montage conseillé :

```text
Onduleur RS232 TX ──┬──> RX convertisseur ESP32-C3
                    └──> RX passerelle IP/RS232

Onduleur RS232 RX <──── non connecté en usage normal/debug passif
GND commun obligatoire
```

Dans cette configuration, l’ESPHome continue de publier vers Home Assistant et la passerelle permet de capturer le flux avec `passive_capture.py` sans émettre vers l’onduleur.

À éviter en usage normal : laisser le TX de la passerelle connecté vers l’onduleur. Cela peut provoquer des collisions, des réponses difficiles à corréler, ou des modifications involontaires si un outil externe envoie des requêtes.

Le TX de la passerelle ne doit être connecté que pour un test actif volontaire et documenté. Voir `docs/GATEWAY_PARALLEL_DEBUG.md`.

## Organisation des fichiers

```text
original.yaml                         Fichier fourni, non modifié
backup/original.yaml                  Sauvegarde du fichier original
configs/production.yaml               Configuration ESPHome de production, RX-only, parser intégré
configs/debug.yaml                    Configuration ESPHome de debug, RX-only, parser + blocs hex
configs/debug-stream-gateway.yaml     Firmware debug passerelle TCP brute sur le port 6666
scripts/jsd_rtu.py                    Fonctions CRC/décodage RTU
scripts/passive_capture.py            Capture passive TCP depuis passerelle IP/RS232
scripts/analyze_capture.py            Analyse synthétique des captures JSONL
scripts/active_read_probe.py          Probe Modbus read-only, expérimental
docs/PASSIVE_CAPTURE_REPORT.md        Rapport de capture passive
docs/WIRING_DIAGRAM.md                Schéma de branchement détaillé
docs/assets/jsd-j6500hc-wiring.png    Image PNG du câblage
docs/ACTIVE_PROBE_REPORT.md           Rapport du probe actif
docs/ARTICLE_DOSSIER.md               Dossier narratif pour futur article
docs/TECHNICAL_DOCUMENTATION.md       Ce document
```

## Configuration de production

Chemin :

```text
/root/.hermes/projects/esphome-jsdsolar-j6500hc/configs/production.yaml
```

Propriétés :

- RX-only ;
- pas de `tx_pin` ;
- noms d’entités Home Assistant conservés ;
- fonctionnement aligné avec le fichier original ;
- destiné à l’usage quotidien.

## Configuration de debug

Chemin :

```text
/root/.hermes/projects/esphome-jsdsolar-j6500hc/configs/debug.yaml
```

Différences principales :

- niveau de log ESPHome : `DEBUG` ;
- ajout de text sensors exposant des blocs hex bruts ;
- utile pour corréler les valeurs reçues avec l’écran de l’onduleur.

Capteurs debug ajoutés :

```text
JSD Debug bloc seq 1 hex
JSD Debug bloc seq 2 hex
JSD Debug bloc seq 3 hex
JSD Debug bloc seq 4 hex
JSD Debug températures hex
JSD Debug bloc seq 14 hex
JSD Debug bloc seq 15 hex
JSD Debug bloc seq 16 hex
```

## Firmware debug passerelle TCP 6666

Chemin :

```text
/root/.hermes/projects/esphome-jsdsolar-j6500hc/configs/debug-stream-gateway.yaml
```

Ce fichier est un firmware alternatif : il expose l’UART RS232 en TCP brut sur le port `6666` via `stream_server`.

Il ne doit pas être combiné avec `production.yaml` ou `debug.yaml`, car le parser passif et `stream_server` consommeraient le même UART.

Propriétés :

- IP prévue : `192.168.x.x` ;
- port TCP brut : `6666` ;
- RX : `GPIO20` ;
- TX : `GPIO21` ;
- pas de publication des mesures JSD décodées ;
- destiné aux captures externes et aux tests actifs volontaires.

Attention : avec `tx_pin: GPIO21`, tout client TCP peut envoyer des octets vers l’onduleur via le port 6666.

Voir `docs/DEBUG_STREAM_GATEWAY.md`.

## Capture passive

Commande :

```bash
cd /root/.hermes/projects/esphome-jsdsolar-j6500hc/scripts
python3 passive_capture.py --host 192.168.x.x --port 6666 --seconds 120 --out ../captures/passive.jsonl
python3 analyze_capture.py ../captures/passive.jsonl
```

La capture passive ne transmet rien sur le bus. Elle lit uniquement les octets reçus depuis la passerelle IP/RS232.

## Probe actif read-only

Commande :

```bash
cd /root/.hermes/projects/esphome-jsdsolar-j6500hc/scripts
python3 active_read_probe.py --host 192.168.x.x --port 6666 --function 3 --out ../captures/fc03_probe.jsonl
python3 active_read_probe.py --host 192.168.x.x --port 6666 --function 4 --out ../captures/fc04_probe.jsonl
```

Attention : ce script envoie des requêtes Modbus de lecture. Il n’écrit pas de registre, mais il utilise TX. Il doit rester expérimental.

Dans les tests réalisés, ce probe n’a pas permis d’obtenir une corrélation fiable, car le flux spontané de l’onduleur continue pendant les requêtes.

## État des validations

| Élément | Statut |
|---|---|
| Fichier original sauvegardé | OK |
| Production YAML créée | OK |
| Debug YAML créée | OK |
| Capture passive effectuée | OK |
| CRC capture passive | 62/62 valides |
| Erreurs de séquence passives | 0 |
| Probe actif read-only | non concluant |
| Compilation ESPHome locale | non testée, ESPHome absent de l’environnement |

## Valeurs observées pendant la capture passive

| Mesure | Valeur approximative | Statut |
|---|---:|---|
| Tension secteur | 242 V | plausible |
| Fréquence secteur | 50.03 Hz | plausible |
| Puissance secteur | 0 W | plausible |
| Tension sortie | 230 V | plausible |
| Puissance sortie | 2.4–2.6 kW | plausible |
| Tension batterie | 47.3–47.5 V | plausible |
| Courant batterie | 54–60 A | plausible |
| SOC batterie | 13 % | plausible |
| Tension PV1 | ~206 V | plausible |
| Courant PV1 | 0 A | plausible |
| Températures | 25.8 / 1.3 / 10.0 °C | suspect |

## Points ouverts

1. Identifier correctement les températures.
2. Identifier le mode de fonctionnement GPB/PBG/PGB/MKS.
3. Identifier les paramètres de configuration de l’onduleur.
4. Obtenir une capture TX/RX séparée ou une corrélation écran fiable.
5. Installer ESPHome dans un environnement adapté pour valider `esphome config` et `esphome compile`.

## Règle de décision pour les futurs mappings

Une valeur sera considérée comme confirmée seulement si elle respecte au moins ces critères :

- trame CRC-valide ;
- position de cycle stable ;
- valeur physiquement plausible ;
- variation corrélée à une observation réelle ;
- comparaison avec écran onduleur ou mesure indépendante ;
- plusieurs points de mesure cohérents.

Une valeur seulement plausible doit rester documentée comme hypothèse.
