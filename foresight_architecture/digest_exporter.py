"""
[DEPRECATED] Use forecast_output.digest_exporter instead.
This file re-exports digest export functions for backward compatibility.
"""

import warnings
warnings.warn(
    "foresight_architecture.digest_exporter is deprecated. Use forecast_output.digest_exporter instead.",
    DeprecationWarning,
    stacklevel=2
)

from forecast_output.digest_exporter import (
    export_digest,
    export_digest_json,
    export_digest_pdf
)