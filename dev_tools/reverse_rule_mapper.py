from simulation_engine.rules.reverse_rule_mapper import load_rule_fingerprints, match_rule_by_delta

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python reverse_rule_mapper.py <fingerprints.json> key1=val1 key2=val2 ...")
        sys.exit(1)
    fingerprints = load_rule_fingerprints(sys.argv[1])
    delta = {}
    for kv in sys.argv[2:]:
        k, v = kv.split("=")
        delta[k] = float(v)
    matches = match_rule_by_delta(delta, fingerprints)
    print("Matches:", matches)