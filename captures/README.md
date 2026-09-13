# Captures

Raw captures are intentionally not committed because they may contain serial numbers, operating data, local IPs or site-specific values.

To create a new capture locally:

```bash
cd scripts
python3 passive_capture.py --host 192.168.x.x --port 6666 --seconds 120 --out ../captures/passive.jsonl
python3 analyze_capture.py ../captures/passive.jsonl
```
