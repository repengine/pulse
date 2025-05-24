"""Manual OPEC Data Plugin.

Reads and processes historical OPEC crude oil price data from a local zip file.

This plugin ingests the OPEC Reference Basket (ORB) price data from a locally stored
zip file (QDL_OPEC_7f41729ade733436c2dc493d282cef69.zip) rather than attempting to
fetch it from the Nasdaq Data Link API.

The plugin:
1. Looks for the zip file in the data/manual_bulk_data directory
2. Extracts and processes any CSV files contained in the zip
3. Creates signals with the name "orb_price" that will be available to the Pulse system
4. Saves processed data to disk for future reference

This approach provides a reliable alternative to API-based ingestion, especially
when the original data source is no longer accessible or requires credentials.

Requires:
- The QDL_OPEC_7f41729ade733436c2dc493d282cef69.zip file in data/manual_bulk_data/
"""

import datetime as dt
import logging
import os
import zipfile
import csv
from typing import Dict, List, Any

from iris.iris_plugins import IrisPluginManager
from iris.iris_utils.ingestion_persistence import save_processed_data

logger = logging.getLogger(__name__)

# Source name for persistence
_SOURCE_NAME = "manual_opec"

# Path to the manual data zip file (relative to the workspace root)
_OPEC_ZIP_PATH = "data/manual_bulk_data/QDL_OPEC_7f41729ade733436c2dc493d282cef69.zip"


class ManualOPECPlugin(IrisPluginManager):
    plugin_name = "manual_opec_plugin"
    enabled = True
    concurrency = 1  # Reading from a local file, no need for high concurrency

    def fetch_signals(self) -> List[Dict[str, Any]]:
        """Fetch OPEC data signals from the local zip file."""
        signals = []

        if not os.path.exists(_OPEC_ZIP_PATH):
            logger.error(f"Manual OPEC data zip file not found at {_OPEC_ZIP_PATH}")
            self.__class__.enabled = False
            return []

        try:
            with zipfile.ZipFile(_OPEC_ZIP_PATH, "r") as zf:
                # Assuming the data file is a CSV inside the zip.
                # We might need to inspect the zip content to confirm the exact filename.
                # For now, let's assume a common naming convention or the first file.
                # A more robust approach would be to check for a file with a .csv extension.
                data_filename = None
                for name in zf.namelist():
                    if name.endswith(".csv"):
                        data_filename = name
                        break

                if not data_filename:
                    logger.error(f"No CSV file found inside {_OPEC_ZIP_PATH}")
                    return []

                with zf.open(data_filename) as infile:
                    # Decode the bytes and read as CSV
                    reader = csv.DictReader(infile.read().decode("utf-8").splitlines())

                    for row in reader:
                        try:
                            # Assuming columns 'date' and 'value' based on reference file
                            date_str = row.get("date")
                            value_str = row.get("value")

                            if not date_str or not value_str:
                                logger.warning(
                                    f"Skipping row with missing date or value: {row}"
                                )
                                continue

                            # Parse date and value
                            timestamp = (
                                dt.datetime.strptime(date_str, "%Y-%m-%d")
                                .replace(tzinfo=dt.timezone.utc)
                                .isoformat()
                            )
                            value = float(value_str)

                            signal = {
                                "name": "orb_price",  # Pulse variable name for OPEC Reference Basket
                                "value": value,
                                "source": _SOURCE_NAME,
                                "timestamp": timestamp,
                                "dataset_id": "OPEC/ORB",  # Use the original Nasdaq dataset ID for consistency
                                "metadata": row,  # Include original row data in metadata
                            }

                            signals.append(signal)

                            # Optional: Save processed data incrementally if the file is very large
                            # This would require modifying save_processed_data or implementing
                            # a similar incremental save logic here. For now, we'll process all
                            # and save at the end or rely on the existing save_processed_data
                            # which might handle lists.

                        except (ValueError, KeyError, TypeError) as e:
                            logger.warning(f"Could not process row {row}: {e}")

        except FileNotFoundError:
            logger.error(f"Manual OPEC data zip file not found at {_OPEC_ZIP_PATH}")
            self.__class__.enabled = False
            return []
        except zipfile.BadZipFile:
            logger.error(f"Invalid zip file: {_OPEC_ZIP_PATH}")
            self.__class__.enabled = False
            return []
        except Exception as e:
            logger.error(f"An error occurred while processing {_OPEC_ZIP_PATH}: {e}")
            self.__class__.enabled = False
            return []

        # After processing all data, save the collected signals
        if signals:
            # The save_processed_data function expects a single item or a list.
            # We can save the entire list here if it's not excessively large,
            # or modify save_processed_data to handle appending to a file.
            # Given the previous incremental saving work, let's assume save_processed_data
            # can handle a list and we'll save the whole batch at the end of fetch_signals.
            # If the file is truly massive, we'd need a different approach (e.g., writing
            # directly to a database or a different file format incrementally).
            # For now, let's save the whole list.
            logger.info(f"Saving {len(signals)} processed signals for manual_opec")
            save_processed_data(
                "OPEC/ORB",  # Use the dataset ID
                signals,
                source_name=_SOURCE_NAME,
                timestamp=dt.datetime.now(dt.timezone.utc).isoformat(),
            )

        return signals


# Example of how to register the plugin (would be done in IrisPluginManager setup)
# mgr = IrisPluginManager()
# mgr.register_plugin(ManualOPECPlugin)
# signals = mgr.run_plugins()
# print(signals)
