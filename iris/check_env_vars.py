"""Environment Variable Checker

This script checks if the required API keys and credentials
for Pulse plugins are properly set in the environment.
"""
import os

def check_env_vars():
    """Check for required environment variables and their values."""
    required_vars = {
        "ALPHA_VANTAGE_KEY": "Financial data API key",
        "FRED_API_KEY": "FRED economic data API key",
        "FINNHUB_API_KEY": "Finnhub financial API key",
        "NASDAQ_API_KEY": "NASDAQ data API key",
        "REDDIT_CLIENT_ID": "Reddit API client ID",
        "REDDIT_CLIENT_SECRET": "Reddit API client secret",
        "REDDIT_USER_AGENT": "Reddit API user agent",
        "NEWS_API_KEY": "News API key",
        "GITHUB_TOKEN": "GitHub API token"
    }
    
    print("===== CHECKING ENVIRONMENT VARIABLES =====\n")
    
    all_set = True
    for var, description in required_vars.items():
        value = os.getenv(var, "")
        masked_value = "***" + value[-4:] if value and len(value) > 4 else ""
        status = "✓ SET" if value else "✗ NOT SET"
        
        if not value:
            all_set = False
        
        if value:
            print(f"{var}: {status} ({masked_value})")
        else:
            print(f"{var}: {status}")
    
    print("\n===== SUMMARY =====")
    if all_set:
        print("All required environment variables are set!")
    else:
        print("Some required environment variables are missing!")

if __name__ == "__main__":
    check_env_vars()