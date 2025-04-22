# cli_trace_audit.py

"""
CLI for trace_audit_engine

Usage:
  python -m memory.trace_audit_engine --replay <trace_id>
  python -m memory.trace_audit_engine --summarize <trace_id>
  python -m memory.trace_audit_engine --audit-all
"""

import sys
from memory.trace_audit_engine import replay_trace, summarize_trace, audit_all_traces

if __name__ == "__main__":
    args = sys.argv[1:]

    if "--replay" in args:
        tid = args[args.index("--replay") + 1]
        replay_trace(tid)
    elif "--summarize" in args:
        tid = args[args.index("--summarize") + 1]
        summarize_trace(tid)
    elif "--audit-all" in args:
        audit_all_traces()
    else:
        print("Usage:")
        print("  python -m memory.trace_audit_engine --replay <trace_id>")
        print("  python -m memory.trace_audit_engine --summarize <trace_id>")
        print("  python -m memory.trace_audit_engine --audit-all")
