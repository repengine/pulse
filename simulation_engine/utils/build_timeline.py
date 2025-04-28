import argparse
import json
import os

def main():
    parser = argparse.ArgumentParser(description="Build timeline from individual JSON snapshots")
    parser.add_argument('--input-dir', required=True, help='Path to directory containing JSON snapshots')
    parser.add_argument('--output-path', required=True, help='Path to write combined JSON file')
    args = parser.parse_args()

    files = [f for f in os.listdir(args.input_dir) if f.endswith('.json')]
    files.sort()
    timeline = []
    for filename in files:
        file_path = os.path.join(args.input_dir, filename)
        with open(file_path, 'r') as f:
            snapshot = json.load(f)
        timeline.append(snapshot)

    with open(args.output_path, 'w') as out_f:
        json.dump(timeline, out_f, indent=2)

if __name__ == "__main__":
    main()