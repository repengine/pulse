#!/usr/bin/env python
"""
API Key Testing Script

Tests whether the system can properly access FRED, Finnhub, and NASDAQ API keys
using both naming conventions (KEY and API_KEY).
"""

import os
import requests
import time
from datetime import datetime
import sys

def mask_key(key):
    """Mask API key for security when displaying"""
    if not key:
        return None
    if len(key) <= 8:
        return key[:2] + '*' * (len(key) - 2)
    return key[:4] + '*' * (len(key) - 8) + key[-4:]

def check_environment_variable(name):
    """Check if an environment variable exists and return its value"""
    value = os.environ.get(name)
    return {
        'name': name,
        'exists': value is not None,
        'value': value,
        'masked': mask_key(value) if value else None
    }

def test_fred_api(api_key):
    """Test a basic FRED API call"""
    url = f"https://api.stlouisfed.org/fred/series?series_id=GDP&api_key={api_key}&file_type=json"
    try:
        response = requests.get(url, timeout=10)
        assert response.status_code == 200, f"FRED API test failed with status code {response.status_code}"
        # Optionally, assert on the content of the response if needed
    except Exception as e:
        assert False, f"Error during FRED API test: {str(e)}"

def test_finnhub_api(api_key):
    """Test a basic Finnhub API call"""
    url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={api_key}"
    try:
        response = requests.get(url, timeout=10)
        assert response.status_code == 200, f"Finnhub API test failed with status code {response.status_code}"
        # Optionally, assert on the content of the response if needed
    except Exception as e:
        assert False, f"Error during Finnhub API test: {str(e)}"

def test_nasdaq_api(api_key):
    """Test a basic NASDAQ Data Link API call"""
    url = f"https://data.nasdaq.com/api/v3/datasets/WIKI/AAPL/data.json?api_key={api_key}&limit=1"
    try:
        response = requests.get(url, timeout=10)
        assert response.status_code == 200, f"NASDAQ API test failed with status code {response.status_code}"
        # Optionally, assert on the content of the response if needed
    except Exception as e:
        assert False, f"Error during NASDAQ API test: {str(e)}"

def print_separator():
    """Print a separator line for readability"""
    print("-" * 80)

def format_result(api_name, env_check, api_test=None):
    """Format and print results for an API key check"""
    success_symbol = "✓" if env_check['exists'] else "✗"
    status = f"[{success_symbol}] {api_name} ({env_check['name']}): "
    
    if env_check['exists']:
        status += f"Found - {env_check['masked']}"
        if api_test:
            api_success = "✓" if api_test['success'] else "✗"
            status += f" - API Test: [{api_success}] {api_test['message']}"
    else:
        status += "Not found"
    
    return status

def main():
    """Main function to test API keys"""
    print("\nAPI KEY TESTING REPORT")
    print("=====================\n")
    print(f"Test run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_separator()
    
    # Check both naming conventions for each API
    apis = [
        {
            'name': 'FRED',
            'env_vars': ['FRED_API_KEY', 'FRED_KEY'],
            'test_func': test_fred_api
        },
        {
            'name': 'Finnhub',
            'env_vars': ['FINNHUB_API_KEY', 'FINNHUB_KEY'],
            'test_func': test_finnhub_api
        },
        {
            'name': 'NASDAQ',
            'env_vars': ['NASDAQ_API_KEY', 'NASDAQ_KEY'],
            'test_func': test_nasdaq_api
        }
    ]
    
    all_success = True
    
    for api in apis:
        print(f"\n{api['name']} API")
        print("-" * (len(api['name']) + 5))
        
        api_success = False
        
        for env_var in api['env_vars']:
            env_check = check_environment_variable(env_var)
            
            if env_check['exists']:
                # Call the test function, which now uses assertions
                api['test_func'](env_check['value'])
                print(format_result(api['name'], env_check, {'success': True, 'message': 'Passed'})) # Assuming test_func raises exception on failure
                api_success = True
            else:
                print(format_result(api['name'], env_check))
        
        if not api_success and any(check_environment_variable(env_var)['exists'] for env_var in api['env_vars']):
            all_success = False
            print(f"WARNING: {api['name']} API key exists but all connection tests failed")
    
    print_separator()
    if all_success:
        print("\nSUMMARY: All available API keys were successfully verified.")
    else:
        print("\nSUMMARY: Some API key tests failed. Please check the detailed results above.")
    
    print("\nNOTE: This script checks both naming conventions (KEY and API_KEY) for each service.")
    print("      The API connection tests verify if the keys are valid and working correctly.")
    print_separator()
    
    # The script itself should not return a value for pytest,
    # but the main function can return an exit code for command line execution.
    return 0 if all_success else 1

if __name__ == "__main__":
    sys.exit(main())