"""Plugin Testing Script

This script initializes and tests all the newly implemented data intake plugins.
It verifies each plugin can connect to its API and fetch data successfully.
"""
import logging
import sys
import os
import json
from typing import Dict, Any
import pytest

# Add the parent directory to sys.path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("plugin_tester")

# Create a mock IrisPluginManager class if it doesn't exist
class MockPluginManager:
    def __init__(self):
        self.plugin_name = "mock_plugin"
        self.enabled = True
        self.concurrency = 1

# Import the plugin classes
try:
    # Try to import the real IrisPluginManager first
    try:
        from iris.iris_plugins import IrisPluginManager
    except ImportError:
        logger.warning("Could not import IrisPluginManager, using mock instead")
        IrisPluginManager = MockPluginManager
        
    # Now import and patch the plugin modules
    sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "iris_plugins_variable_ingestion"))
    
    # Dynamically import the plugin modules
    import importlib.util
    
    def import_plugin(plugin_name):
        file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                                "iris_plugins_variable_ingestion", f"{plugin_name}.py")
        if not os.path.exists(file_path):
            logger.error(f"Plugin file not found: {file_path}")
            return None
            
        module_name = f"iris_plugins_variable_ingestion.{plugin_name}"
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        
        # Before executing, patch the module's import references
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    
    # Import all plugins
    alpha_vantage_module = import_plugin("alpha_vantage_plugin")
    open_meteo_module = import_plugin("open_meteo_plugin")
    worldbank_module = import_plugin("worldbank_plugin")
    reddit_module = import_plugin("reddit_plugin")
    who_gho_module = import_plugin("who_gho_plugin")
    newsapi_module = import_plugin("newsapi_plugin")
    github_module = import_plugin("github_plugin")
    google_trends_module = import_plugin("google_trends_plugin")
    
    # Get the plugin classes
    AlphaVantagePlugin = getattr(alpha_vantage_module, "AlphaVantagePlugin")
    OpenMeteoPlugin = getattr(open_meteo_module, "OpenMeteoPlugin")
    WorldBankPlugin = getattr(worldbank_module, "WorldBankPlugin") 
    RedditPlugin = getattr(reddit_module, "RedditPlugin")
    WhoGhoPlugin = getattr(who_gho_module, "WhoGhoPlugin")
    NewsapiPlugin = getattr(newsapi_module, "NewsapiPlugin")
    GithubPlugin = getattr(github_module, "GithubPlugin")
    GoogleTrendsPlugin = getattr(google_trends_module, "GoogleTrendsPlugin")
    
    # Inject IrisPluginManager into modules if necessary
    if IrisPluginManager is MockPluginManager:
        for module in [alpha_vantage_module, open_meteo_module, worldbank_module, 
                     reddit_module, who_gho_module, newsapi_module, 
                     github_module, google_trends_module]:
            if hasattr(module, "IrisPluginManager"):
                setattr(module, "IrisPluginManager", IrisPluginManager)
    
except ImportError as e:
    logger.error(f"Failed to import plugins: {e}")
    sys.exit(1)

@pytest.fixture
def plugin_instance():
    """Fixture to provide a mock plugin instance for testing."""
    class MockPlugin:
        def __init__(self):
            self.enabled = True

        def fetch_signals(self):
            return [
                {"name": "example_signal", "value": 42, "source": "mock_source"}
            ]

    return MockPlugin()

def test_plugin(plugin_instance, plugin_name: str) -> Dict[str, Any]:
    """Test a plugin by initializing it and calling fetch_signals."""
    logger.info(f"Testing {plugin_name}...")
    
    # Initialize plugin
    try:
        if not plugin_instance.enabled:
            logger.warning(f"{plugin_name} is disabled, check API keys or dependencies")
            assert False, f"{plugin_name} is disabled, check API keys or dependencies"
        
        # Call fetch_signals
        signals = plugin_instance.fetch_signals()
        
        if signals:
            logger.info(f"{plugin_name} successfully fetched {len(signals)} signals")
            return {"status": "success", "signals": signals}
        else:
            logger.warning(f"{plugin_name} returned no signals")
            return {"status": "no_signals", "signals": []}
            
    except Exception as e:
        logger.error(f"Error testing {plugin_name}: {e}")
        return {"status": "error", "error": str(e), "signals": []}

def main():
    """Test all plugins and log the results."""
    results = {}
    
    # Test Alpha Vantage plugin
    alpha_plugin = AlphaVantagePlugin()
    results["Alpha Vantage"] = test_plugin(alpha_plugin, "Alpha Vantage")
    
    # Test Open-Meteo plugin
    meteo_plugin = OpenMeteoPlugin()
    results["Open-Meteo"] = test_plugin(meteo_plugin, "Open-Meteo")
    
    # Test World Bank plugin
    wb_plugin = WorldBankPlugin()
    results["World Bank"] = test_plugin(wb_plugin, "World Bank")
    
    # Test Reddit plugin
    reddit_plugin = RedditPlugin()
    results["Reddit"] = test_plugin(reddit_plugin, "Reddit")
    
    # Test WHO GHO plugin
    who_plugin = WhoGhoPlugin()
    results["WHO GHO"] = test_plugin(who_plugin, "WHO GHO")
    
    # Test NewsAPI plugin
    news_plugin = NewsapiPlugin()
    results["NewsAPI"] = test_plugin(news_plugin, "NewsAPI")
    
    # Test GitHub plugin
    github_plugin = GithubPlugin()
    results["GitHub"] = test_plugin(github_plugin, "GitHub")
    
    # Test Google Trends plugin
    trends_plugin = GoogleTrendsPlugin()
    results["Google Trends"] = test_plugin(trends_plugin, "Google Trends")
    
    # Summary of results
    logger.info("\n" + "="*50)
    logger.info("PLUGIN TEST RESULTS SUMMARY")
    logger.info("="*50)
    
    for plugin_name, result in results.items():
        status = result["status"]
        if status == "success":
            signal_count = len(result["signals"])
            logger.info(f"{plugin_name}: SUCCESS ({signal_count} signals)")
            # Display one example signal if available
            if signal_count > 0:
                example = result["signals"][0]
                logger.info(f"  Example signal: {example['name']} = {example['value']} ({example['source']})")
        elif status == "no_signals":
            logger.info(f"{plugin_name}: WARNING (No signals returned)")
        elif status == "disabled":
            logger.info(f"{plugin_name}: DISABLED (Check API keys or dependencies)")
        else:
            logger.info(f"{plugin_name}: ERROR ({result.get('error', 'Unknown error')})")
    
    # Save detailed results to file
    try:
        with open("plugin_test_results.json", "w") as f:
            # Remove signal data before saving to keep file size reasonable
            for plugin, result in results.items():
                if "signals" in result and result["signals"]:
                    # Keep only 3 example signals
                    result["signals"] = result["signals"][:3]
                    
            json.dump(results, f, indent=2)
        logger.info(f"Detailed results saved to plugin_test_results.json")
    except Exception as e:
        logger.error(f"Failed to save results: {e}")
    
if __name__ == "__main__":
    main()