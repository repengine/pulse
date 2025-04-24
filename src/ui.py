"""
Consolidated UI module: interactive shells & operator interfaces.
"""

# Interactive shells
from pulse_interactive_shell import run_shell as interactive_shell
from pulse_ui_shell import run_shell as ui_shell
from pulse_ui_operator import run_shell as ui_operator

# Operator interface modules
import operator_interface.learning_log_viewer as learning_log_viewer
import operator_interface.mutation_digest_exporter as mutation_digest_exporter
import operator_interface.mutation_log_viewer as mutation_log_viewer
import operator_interface.operator_brief_generator as operator_brief_generator
import operator_interface.pulse_prompt_logger as pulse_prompt_logger
import operator_interface.rule_cluster_digest_formatter as rule_cluster_digest_formatter
import operator_interface.rule_cluster_viewer as rule_cluster_viewer
import operator_interface.strategos_digest as strategos_digest
import operator_interface.symbolic_contradiction_digest as symbolic_contradiction_digest
import operator_interface.symbolic_revision_report as symbolic_revision_report
import operator_interface.variable_cluster_digest_formatter as variable_cluster_digest_formatter
# CLI dev_tools modules
import dev_tools.cli_retrodict_forecasts as cli_retrodict_forecasts
import dev_tools.cli_trace_audit as cli_trace_audit
import dev_tools.operator_brief_cli as operator_brief_cli
import dev_tools.pulse_arc_cli as pulse_arc_cli

__all__ = [
    "interactive_shell",
    "ui_shell",
    "ui_operator",
    "learning_log_viewer",
    "mutation_digest_exporter",
    "mutation_log_viewer",
    "operator_brief_generator",
    "pulse_prompt_logger",
    "rule_cluster_digest_formatter",
    "rule_cluster_viewer",
    "strategos_digest",
    "symbolic_contradiction_digest",
    "symbolic_revision_report",
    "variable_cluster_digest_formatter",
    "cli_retrodict_forecasts",
    "cli_trace_audit",
    "operator_brief_cli",
    "pulse_arc_cli",
]