import json

def load_rule_fingerprints(path):
    with open(path, "r") as f:
        return json.load(f)

def match_rule_fingerprint(rule_fingerprints, target_fingerprint):
    """
    Given a list of rule fingerprints and a target, return the matching rule or None.
    """
    for rule in rule_fingerprints:
        if rule.get('fingerprint') == target_fingerprint:
            return rule
    return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python reverse_rule_mapper.py <fingerprints.json> <target_fingerprint>")
        sys.exit(1)
    fingerprints = load_rule_fingerprints(sys.argv[1])
    match = match_rule_fingerprint(fingerprints, sys.argv[2])
    if match:
        print("Matched rule:", match)
    else:
        print("No match found.")