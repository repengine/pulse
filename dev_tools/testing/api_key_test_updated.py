#!/usr/bin/env python
"""
API Key Testing Script (Updated)

Tests whether the system can properly access FRED, Finnhub, and NASDAQ API keys
using both naming conventions (KEY and API_KEY) with enhanced error reporting.
"""

import os
import requests
import json
from datetime import datetime
import sys


def mask_key(key):
    """Mask API key for security when displaying"""
    if not key:
        return None
    if len(key) <= 8:
        return key[:2] + "*" * (len(key) - 2)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


def check_environment_variable(name):
    """Check if an environment variable exists and return its value"""
    value = os.environ.get(name)
    return {
        "name": name,
        "exists": value is not None,
        "value": value,
        "masked": mask_key(value) if value else None,
    }


def test_fred_api(api_key):
    """Test a basic FRED API call"""
    url = f"https://api.stlouisfed.org/fred/series?series_id=GDP&api_key={api_key}&file_type=json"
    try:
        response = requests.get(url, timeout=10)
        content = {}
        try:
            if response.status_code != 200:
                content = response.json()
            else:
                content = {"series_id": "GDP", "success": True}
        except Exception:  # Catching general exception, consider more specific if known
            content = {
                "text": response.text[:100] + "..."
                if len(response.text) > 100
                else response.text
            }

        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "message": "Success"
            if response.status_code == 200
            else f"Failed with status {response.status_code}",
            "content": content,
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": None,
            "message": f"Error: {str(e)}",
            "content": {},
        }


def test_finnhub_api(api_key):
    """Test a basic Finnhub API call"""
    url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={api_key}"
    try:
        response = requests.get(url, timeout=10)
        content = {}
        try:
            if response.status_code == 200:
                content = response.json()
                # Just keep the keys for display, not the actual values
                content = {k: "..." for k in content.keys()} if content else {}
            else:
                content = response.json()
        except Exception:  # Catching general exception, consider more specific if known
            content = {
                "text": response.text[:100] + "..."
                if len(response.text) > 100
                else response.text
            }

        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "message": "Success"
            if response.status_code == 200
            else f"Failed with status {response.status_code}",
            "content": content,
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": None,
            "message": f"Error: {str(e)}",
            "content": {},
        }


def test_nasdaq_api(api_key):
    """Test a basic NASDAQ Data Link API call with alternative endpoints"""
    # Initialize these variables before the loop to ensure they're always defined
    last_status_code = None
    last_error_msg = "All endpoints failed - no connection attempts made"
    last_content = {}

    # Define the endpoints to try
    endpoints = [
        {
            "name": "WIKI AAPL",
            "url": f"https://data.nasdaq.com/api/v3/datasets/WIKI/AAPL/data.json?api_key={api_key}&limit=1",
        },
        {
            "name": "Alternative endpoint - ECB Exchange Rates",
            "url": f"https://data.nasdaq.com/api/v3/datasets/ECB/EURUSD.json?api_key={api_key}&limit=1",
        },
        {
            "name": "List databases - requires premium",
            "url": f"https://data.nasdaq.com/api/v3/databases?api_key={api_key}",
        },
    ]

    # Try each endpoint
    for endpoint in endpoints:
        try:
            print(f"  Trying NASDAQ endpoint: {endpoint['name']}")
            response = requests.get(endpoint["url"], timeout=10)
            content = {}

            # Try to parse the response as JSON
            try:
                content = response.json()

                # Check if the request was successful
                if response.status_code == 200:
                    # Summarize the content for display
                    display_content = {}
                    if "dataset_data" in content:
                        display_content = {
                            "dataset_data": "Found",
                            "columns": len(
                                content.get("dataset_data", {}).get("column_names", [])
                            ),
                        }
                    elif "dataset" in content:
                        display_content = {
                            "dataset": "Found",
                            "id": content.get("dataset", {}).get("id", "N/A"),
                        }
                    else:
                        display_content = {k: "..." for k in content.keys()}

                    # Successful API call
                    return {
                        "success": True,
                        "status_code": 200,
                        "message": f"Success with endpoint: {endpoint['name']}",
                        "content": display_content,
                    }

                # Handle error response
                error_msg = f"Failed with status {response.status_code}"

                # Extract more detailed error message if available
                if isinstance(content, dict) and "quandl_error" in content:
                    quandl_error = content.get("quandl_error", {})
                    if isinstance(quandl_error, dict) and "message" in quandl_error:
                        error_msg += f" - {quandl_error['message']}"

                # Save the error details for later
                last_status_code = response.status_code
                last_error_msg = error_msg
                last_content = content

            except Exception:
                # Failed to parse JSON
                text_preview = (
                    response.text[:100] + "..."
                    if len(response.text) > 100
                    else response.text
                )
                last_status_code = response.status_code
                last_error_msg = f"Failed with status {response.status_code} - Could not parse response"
                last_content = {"text": text_preview}

        except Exception as request_error:
            # Connection error
            last_error_msg = f"Connection error: {str(request_error)}"

    # If we've tried all endpoints and none succeeded, return the last error
    return {
        "success": False,
        "status_code": last_status_code,
        "message": last_error_msg,
        "content": last_content,
    }


def print_separator():
    """Print a separator line for readability"""
    print("-" * 80)


def format_result(api_name, env_check, api_test=None):
    """Format and print results for an API key check"""
    success_symbol = "✓" if env_check["exists"] else "✗"
    status = f"[{success_symbol}] {api_name} ({env_check['name']}): "

    if env_check["exists"]:
        status += f"Found - {env_check['masked']}"
        if api_test:
            api_success = "✓" if api_test["success"] else "✗"
            status += f" - API Test: [{api_success}] {api_test['message']}"
            if api_test["content"] and not api_test["success"]:
                # Format the content for display
                try:
                    content_str = json.dumps(api_test["content"], indent=2)
                    status += f"\n    Response: {content_str}"
                except Exception:  # Catching general exception, consider more specific if known
                    status += f"\n    Response: {api_test['content']}"
    else:
        status += "Not found"

    return status


def main():
    """Main function to test API keys"""
    print("\nAPI KEY TESTING REPORT (ENHANCED)")
    print("===============================\n")
    print(f"Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator()

    # Check both naming conventions for each API
    apis = [
        {
            "name": "FRED",
            "env_vars": ["FRED_API_KEY", "FRED_KEY"],
            "test_func": test_fred_api,
        },
        {
            "name": "Finnhub",
            "env_vars": ["FINNHUB_API_KEY", "FINNHUB_KEY"],
            "test_func": test_finnhub_api,
        },
        {
            "name": "NASDAQ",
            "env_vars": ["NASDAQ_API_KEY", "NASDAQ_KEY"],
            "test_func": test_nasdaq_api,
        },
    ]

    all_success = True

    for api in apis:
        print(f"\n{api['name']} API")
        print("-" * (len(api["name"]) + 5))

        api_success = False

        for env_var in api["env_vars"]:
            env_check = check_environment_variable(env_var)

            if env_check["exists"]:
                api_test = api["test_func"](env_check["value"])
                print(format_result(api["name"], env_check, api_test))
                if api_test["success"]:
                    api_success = True
            else:
                print(format_result(api["name"], env_check))

        if not api_success and any(
            check_environment_variable(env_var)["exists"] for env_var in api["env_vars"]
        ):
            all_success = False
            print(
                f"WARNING: {api['name']} API key exists but all connection tests failed"
            )

    print_separator()
    if all_success:
        print("\nSUMMARY: All available API keys were successfully verified.")
    else:
        print(
            "\nSUMMARY: Some API key tests failed. Please check the detailed results above."
        )

    print(
        "\nNOTE: This script checks both naming conventions (KEY and API_KEY) for each service."
    )
    print(
        "      The API connection tests verify if the keys are valid and working correctly."
    )
    print_separator()

    return 0 if all_success else 1


if __name__ == "__main__":
    sys.exit(main())
