"""
Test suite for the capital engine layer.
Tests symbolic-driven capital mutations, exposure calculations, and forecasting.
"""

import pytest
import sys
import os

# Add parent directory to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulation_engine.worldstate import WorldState, CapitalExposure, SymbolicOverlays
from capital_engine.capital_layer import (
    simulate_nvda_fork, simulate_msft_fork, simulate_ibit_fork, simulate_spy_fork,
    run_capital_forks, summarize_exposure, total_exposure, exposure_percentages,
    portfolio_alignment_tags, run_shortview_forecast
)


class TestCapitalForks:
    """Tests for individual capital fork functions."""
    
    @pytest.fixture
    def test_state(self):
        """Create a test world state with default overlays."""
        state = WorldState()
        state.overlays = SymbolicOverlays(
            hope=0.7,    # High hope
            despair=0.3,  # Low despair
            rage=0.2,     # Low rage
            fatigue=0.4,  # Moderate fatigue
            trust=0.8     # High trust
        )
        return state
        
    def test_nvda_fork(self, test_state):
        """Test NVDA capital fork with high hope/trust."""
        simulate_nvda_fork(test_state)
        assert test_state.capital.nvda > 0, "Expected positive NVDA exposure"
        
    def test_msft_fork(self, test_state):
        """Test MSFT capital fork with high trust, low rage."""
        simulate_msft_fork(test_state)
        assert test_state.capital.msft > 0, "Expected positive MSFT exposure"
        
    def test_ibit_fork(self, test_state):
        """Test IBIT capital fork with high hope."""
        simulate_ibit_fork(test_state)
        assert test_state.capital.ibit > 0, "Expected positive IBIT exposure"
        
    def test_spy_fork(self, test_state):
        """Test SPY capital fork with high trust and hope."""
        simulate_spy_fork(test_state)
        assert test_state.capital.spy > 0, "Expected positive SPY exposure"
        
    def test_run_all_forks(self, test_state):
        """Test running all capital forks."""
        run_capital_forks(test_state)
        assert test_state.capital.nvda > 0, "NVDA should have exposure"
        assert test_state.capital.msft > 0, "MSFT should have exposure"
        assert test_state.capital.ibit > 0, "IBIT should have exposure"
        assert test_state.capital.spy > 0, "SPY should have exposure"
        
    def test_run_selective_forks(self, test_state):
        """Test running only selected capital forks."""
        run_capital_forks(test_state, assets=["nvda", "msft"])
        assert test_state.capital.nvda > 0, "NVDA should have exposure"
        assert test_state.capital.msft > 0, "MSFT should have exposure"
        assert test_state.capital.ibit == 0, "IBIT should have no exposure"
        assert test_state.capital.spy == 0, "SPY should have no exposure"
        
    def test_negative_exposure(self):
        """Test that negative sentiment creates negative exposure."""
        state = WorldState()
        state.overlays = SymbolicOverlays(
            hope=0.3,     # Low hope
            despair=0.8,   # High despair
            rage=0.7,      # High rage
            fatigue=0.7,   # High fatigue
            trust=0.2      # Low trust
        )
        simulate_nvda_fork(state)
        assert state.capital.nvda < 0, "Expected negative NVDA exposure with negative sentiment"


class TestCapitalSummaries:
    """Tests for capital summary and portfolio functions."""
    
    @pytest.fixture
    def portfolio_state(self):
        """Create a test state with an existing portfolio."""
        state = WorldState()
        state.capital = CapitalExposure(
            nvda=10000,
            msft=15000,
            ibit=5000,
            spy=20000,
            cash=50000
        )
        return state
        
    def test_summarize_exposure(self, portfolio_state):
        """Test summarizing exposure as a dictionary."""
        exposure = summarize_exposure(portfolio_state)
        assert exposure["nvda"] == 10000
        assert exposure["msft"] == 15000
        assert exposure["ibit"] == 5000
        assert exposure["spy"] == 20000
        assert exposure["cash"] == 50000
        
    def test_total_exposure(self, portfolio_state):
        """Test calculating total exposure (excluding cash)."""
        total = total_exposure(portfolio_state)
        assert total == 50000  # 10000 + 15000 + 5000 + 20000
        
    def test_exposure_percentages(self, portfolio_state):
        """Test calculating exposure percentages."""
        percentages = exposure_percentages(portfolio_state)
        assert percentages["nvda"] == 0.2  # 10000/50000
        assert percentages["msft"] == 0.3  # 15000/50000
        assert percentages["ibit"] == 0.1  # 5000/50000
        assert percentages["spy"] == 0.4   # 20000/50000
        assert "cash" not in percentages
        
    def test_portfolio_alignment_tags(self):
        """Test portfolio alignment tags based on overlays."""
        # Test growth-aligned
        state = WorldState()
        state.overlays.trust = 0.7  # High trust -> growth-aligned
        tags = portfolio_alignment_tags(state)
        assert tags["bias"] == "growth-aligned"
        
        # Test defensive
        state.overlays.trust = 0.5
        state.overlays.fatigue = 0.6  # High fatigue -> defensive
        tags = portfolio_alignment_tags(state)
        assert tags["bias"] == "defensive"
        
        # Test neutral
        state.overlays.trust = 0.5
        state.overlays.fatigue = 0.4
        tags = portfolio_alignment_tags(state)
        assert tags["bias"] == "neutral"


class TestShortviewForecast:
    """Tests for the shortview forecast functionality."""
    
    @pytest.fixture
    def forecast_state(self):
        """Create a test state for forecasting."""
        state = WorldState()
        state.overlays = SymbolicOverlays(
            hope=0.6, despair=0.4, rage=0.3, fatigue=0.4, trust=0.6
        )
        state.capital = CapitalExposure(cash=100000)
        return state
        
    def test_basic_forecast(self, forecast_state):
        """Test running a basic shortview forecast."""
        forecast = run_shortview_forecast(forecast_state, duration_days=2)
        
        # Check that forecast has all required keys
        assert "duration_days" in forecast
        assert "symbolic_fragility" in forecast
        assert "symbolic_change" in forecast
        assert "capital_delta" in forecast
        assert "portfolio_alignment" in forecast
        
        # Check duration is correctly set
        assert forecast["duration_days"] == 2
        
    def test_forecast_validation(self, forecast_state):
        """Test validation of forecast parameters."""
        # Test invalid duration
        with pytest.raises(ValueError):
            run_shortview_forecast(forecast_state, duration_days=8)  # Max is 7
            
        with pytest.raises(ValueError):
            run_shortview_forecast(forecast_state, duration_days=0)  # Min is 1
            
    def test_asset_subset(self, forecast_state):
        """Test forecast with specific asset subset."""
        forecast = run_shortview_forecast(forecast_state, asset_subset=["nvda", "msft"])
        
        # Only NVDA and MSFT should have capital changes
        assert "nvda" in forecast["capital_delta"]
        assert "msft" in forecast["capital_delta"]
        assert "ibit" not in forecast["capital_delta"] or forecast["capital_delta"]["ibit"] == 0
        assert "spy" not in forecast["capital_delta"] or forecast["capital_delta"]["spy"] == 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])
