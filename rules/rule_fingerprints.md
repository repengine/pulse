# Rule Fingerprints Schema

Each entry in `rule_fingerprints.json` must have:
- `"rule_id"`: string, unique rule identifier
- `"effects"`: object mapping variable/overlay names to float values

Example:
```json
[
  {
    "rule_id": "R001",
    "effects": {"hope": 0.1, "despair": -0.05}
  },
  {
    "rule_id": "R002",
    "effects": {"rage": 0.2}
  }
]
```
