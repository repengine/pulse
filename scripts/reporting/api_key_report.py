#!/usr/bin/env python
"""
API Key Testing Script

Tests whether the system can properly access FRED, Finnhub, and NASDAQ API keys
using both naming conventions.
"""

import os
import requests
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
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "message": (
                "Success"
                if response.status_code == 200
                else f"Failed with status {response.status_code}"
            ),
            "details": (
                "API connection successful"
                if response.status_code == 200
                else "See response for details"
            ),
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": None,
            "message": f"Error: {str(e)}",
            "details": "Connection error",
        }


def test_finnhub_api(api_key):
    """Test a basic Finnhub API call"""
    url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={api_key}"
    try:
        response = requests.get(url, timeout=10)
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "message": (
                "Success"
                if response.status_code == 200
                else f"Failed with status {response.status_code}"
            ),
            "details": (
                "API connection successful"
                if response.status_code == 200
                else "See response for details"
            ),
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": None,
            "message": f"Error: {str(e)}",
            "details": "Connection error",
        }


def test_nasdaq_api(api_key):
    """Test a basic NASDAQ Data Link API call with free tier endpoints"""
    # Try free tier endpoint patterns that are more likely to work
    endpoints = [{"name": "LBMA Gold Dataset",
                  "url": f"https://data.nasdaq.com/api/v3/datasets/LBMA/GOLD.json?api_key={api_key}&limit=1",
                  },
                 {"name": "FRED GDP Dataset",
                  "url": f"https://data.nasdaq.com/api/v3/datasets/FRED/GDP.json?api_key={api_key}&limit=1",
                  },
                 {"name": "ODA Aluminum Price",
                  "url": f"https://data.nasdaq.com/api/v3/datasets/ODA/PALUM_USD.json?api_key={api_key}&limit=1",
                  },
                 {"name": "OPEC Reference Basket",
                  "url": f"https://data.nasdaq.com/api/v3/datasets/OPEC/ORB.json?api_key={api_key}&limit=1",
                  },
                 {"name": "World Bank Population",
                  "url": f"https://data.nasdaq.com/api/v3/datasets/WORLDBANK/WLD_SP_POP_TOTL.json?api_key={api_key}&limit=1",
                  },
                 ]

    for endpoint in endpoints:
        try:
            response = requests.get(endpoint["url"], timeout=10)
            if response.status_code == 200:
                return {
                    "success": True,
                    "status_code": 200,
                    "message": f"Success with endpoint: {endpoint['name']}",
                    "details": "API connection successful",
                }
            # Special handling for the 410 Gone status we're seeing
            elif response.status_code == 410:
                return {
                    "success": False,
                    "status_code": 410,
                    "message": f"Endpoint no longer available (410 Gone): {
                        endpoint['name']}",
                    "details": "This suggests the API endpoints have changed or been deprecated. Check NASDAQ Data Link documentation for updated endpoints.",
                }
        except Exception:
            continue

    return {
        "success": False,
        "status_code": None,
        "message": "All endpoints failed",
        "details": "Consider checking the NASDAQ API documentation for updated endpoints or contact their support for assistance.",
    }


def format_result(api_name, key_name, key_value, test_result=None):
    """Format results for display"""
    if key_value:
        result = f"{api_name} ({key_name}): ✓ Found - {mask_key(key_value)}"
        if test_result:
            status = "✓" if test_result["success"] else "✗"
            result += f"\n  Connection test: [{status}] {test_result['message']}"
            result += f"\n  Details: {test_result['details']}"
    else:
        result = f"{api_name} ({key_name}): ✗ Not found"

    return result


def main():
    """Main function to test API keys"""
    print("\nAPI KEY TESTING REPORT")
    print("====================\n")

    # Define the APIs to test
    apis = [
        {
            "name": "FRED",
            "keys": ["FRED_API_KEY", "FRED_KEY"],
            "test_func": test_fred_api,
        },
        {
            "name": "Finnhub",
            "keys": ["FINNHUB_API_KEY", "FINNHUB_KEY"],
            "test_func": test_finnhub_api,
        },
        {
            "name": "NASDAQ",
            "keys": ["NASDAQ_API_KEY", "NASDAQ_KEY"],
            "test_func": test_nasdaq_api,
        },
    ]

    # Summary containers
    results = []
    all_keys_found = True
    all_connections_successful = True

    # Test each API
    for api in apis:
        api_name = api["name"]
        print(f"\n{api_name} API:")
        print("-" * (len(api_name) + 5))

        api_keys_found = False
        api_connections_successful = False

        for key_name in api["keys"]:
            key_value = os.environ.get(key_name)

            if key_value:
                api_keys_found = True
                test_result = api["test_func"](key_value)
                if test_result["success"]:
                    api_connections_successful = True

                print(format_result(api_name, key_name, key_value, test_result))
            else:
                print(format_result(api_name, key_name, None))

        results.append(
            {
                "api": api_name,
                "keys_found": api_keys_found,
                "connections_successful": api_connections_successful,
            }
        )

        all_keys_found = all_keys_found and api_keys_found
        all_connections_successful = (
            all_connections_successful and api_connections_successful
        )

    # Print summary
    print("\n" + "=" * 50)
    print("\nSUMMARY:")
    print("--------")

    for result in results:
        keys_status = "✓" if result["keys_found"] else "✗"
        conn_status = "✓" if result["connections_successful"] else "✗"
        print(f"{result['api']}: Keys [{keys_status}] Connection [{conn_status}]")

    print("\nOVERALL STATUS:")
    if all_keys_found and all_connections_successful:
        print(
            "✅ All API keys found and working correctly with both naming conventions"
        )
    elif all_keys_found and not all_connections_successful:
        print("⚠️ All API keys found, but some connection tests failed")
    elif not all_keys_found:
        print("❌ Some API keys are missing")

    if not all_connections_successful:
        print("\nNOTES:")
        if any(
            r["api"] == "NASDAQ" and not r["connections_successful"] for r in results
        ):
            print(
                "- NASDAQ API: Connection test failed. Your API key may have limited access."
            )
            print(
                "  Try using free tier datasets like 'LBMA/GOLD', 'FRED/GDP', 'ODA/PALUM_USD', or 'OPEC/ORB'."
            )
            print(
                "  Access to premium datasets like 'EOD/AAPL' may require a paid subscription."
            )

    print("\nTest completed at:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 50)

    return 0 if all_keys_found else 1


if __name__ == "__main__":
    sys.exit(main())
