"""
Unit tests for the causal benchmarks script and CLI flag integration.
"""

import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from simulation_engine.batch_runner import run_batch_from_config
from simulation_engine.simulator_core import simulate_forward
from scripts.run_causal_benchmarks import (
    load_scenarios_from_file,
    run_scenario_programmatically,
    calculate_metrics,
    run_causal_benchmarks
)

class TestCausalBenchmarks:
    """Tests for causal benchmarks functionality."""
    
    def test_gravity_off_flag_integration(self):
        """Test that the gravity-off flag is properly passed through the simulation stack."""
        with patch('simulation_engine.batch_runner.simulate_forward') as mock_simulate:
            mock_simulate.return_value = [{'turn': 1, 'deltas': {}}]
            
            # Run with gravity enabled (default)
            run_batch_from_config(
                configs=[{'state_overrides': {'hope': 0.5}, 'turns': 1}],
                gravity_enabled=True
            )
            
            # First call should have gravity_enabled=True
            assert mock_simulate.call_count > 0, "simulate_forward was not called"
            args, kwargs = mock_simulate.call_args
            assert kwargs.get('gravity_enabled') is True, "Gravity should be enabled by default"
            
            mock_simulate.reset_mock()
            
            # Run with gravity disabled
            run_batch_from_config(
                configs=[{'state_overrides': {'hope': 0.5}, 'turns': 1}],
                gravity_enabled=False
            )
            
            # Second call should have gravity_enabled=False
            assert mock_simulate.call_count > 0, "simulate_forward was not called"
            args, kwargs = mock_simulate.call_args
            assert kwargs.get('gravity_enabled') is False, "Gravity should be disabled when flag is passed"

    def test_conditional_gravity_application(self):
        """Test that gravity correction is conditionally applied based on the flag."""
        with patch('symbolic_system.gravity.symbolic_gravity_fabric.create_default_fabric') as mock_fabric_creator, \
             patch('simulation_engine.simulator_core.simulate_turn') as mock_simulate_turn:
            
            # Mock the necessary return values
            mock_simulate_turn.return_value = {'turn': 1, 'deltas': {}}
            
            # Test with gravity enabled
            simulate_forward(
                state=MagicMock(),
                turns=1,
                gravity_enabled=True
            )
            
            # Check that simulate_turn was called with gravity_enabled=True
            assert mock_simulate_turn.call_count > 0, "simulate_turn was not called"
            args, kwargs = mock_simulate_turn.call_args
            assert kwargs.get('gravity_enabled') is True
            
            mock_simulate_turn.reset_mock()
            
            # Test with gravity disabled
            simulate_forward(
                state=MagicMock(),
                turns=1,
                gravity_enabled=False
            )
            
            # Check that simulate_turn was called with gravity_enabled=False
            assert mock_simulate_turn.call_count > 0, "simulate_turn was not called"
            args, kwargs = mock_simulate_turn.call_args
            assert kwargs.get('gravity_enabled') is False

    def test_load_scenarios_from_file(self):
        """Test loading scenarios from a file."""
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            test_scenarios = [
                {
                    "name": "test_scenario",
                    "description": "Test scenario",
                    "configs": [
                        {"state_overrides": {"hope": 0.7}, "turns": 1}
                    ]
                }
            ]
            tmp.write(json.dumps(test_scenarios).encode('utf-8'))
            tmp_path = tmp.name
        
        try:
            # Test loading from the temp file
            scenarios = load_scenarios_from_file(tmp_path)
            assert len(scenarios) == 1
            assert scenarios[0]["name"] == "test_scenario"
            
            # Test loading from non-existent file (should use defaults)
            scenarios = load_scenarios_from_file("non_existent_file.json")
            assert len(scenarios) > 0, "Should return default scenarios for non-existent file"
        finally:
            # Clean up
            os.unlink(tmp_path)

    def test_run_scenario_programmatically(self):
        """Test running a scenario programmatically."""
        scenario = {
            "name": "test_scenario",
            "description": "Test scenario",
            "configs": [
                {"state_overrides": {"hope": 0.7}, "turns": 1}
            ]
        }
        
        with patch('scripts.run_causal_benchmarks.run_batch_from_config') as mock_run_batch:
            mock_run_batch.return_value = [{'forecasts': [{'accuracy': 0.8}]}]
            
            # Run scenario
            result = run_scenario_programmatically(scenario, "test_output.jsonl")
            
            # Check that batch_runner was called with gravity_enabled=False
            args, kwargs = mock_run_batch.call_args
            assert kwargs.get('gravity_enabled') is False, "Gravity should be disabled for causal benchmarks"
            
            # Check result structure
            assert "scenario" in result
            assert "metrics" in result
            assert "timestamp" in result

    def test_calculate_metrics(self):
        """Test the metric calculation function."""
        # Sample simulation results
        results = [
            {
                "forecasts": [
                    {
                        "accuracy": 0.8,
                        "drift": 0.2,
                        "variables": {
                            "var1": {"accuracy": 0.9, "drift": 0.1},
                            "var2": {"accuracy": 0.7, "drift": 0.3}
                        }
                    }
                ]
            }
        ]
        
        scenario = {"name": "test"}
        metrics = calculate_metrics(results, scenario)
        
        # Check metric structure
        assert metrics["accuracy"]["overall"] == 0.8
        assert metrics["drift"]["overall"] == 0.2
        assert "var1" in metrics["accuracy"]["by_variable"]
        assert "var2" in metrics["accuracy"]["by_variable"]
        assert metrics["accuracy"]["by_variable"]["var1"] == 0.9
        assert metrics["drift"]["by_variable"]["var1"] == 0.1
        
        # Check summary metrics
        assert "summary" in metrics
        assert metrics["summary"]["overall_accuracy"] == 0.8
        assert metrics["summary"]["overall_drift"] == 0.2
        assert metrics["summary"]["variable_count"] == 2
        assert metrics["summary"]["best_variable"] == "var1"
        assert metrics["summary"]["worst_variable"] == "var2"

    def test_run_causal_benchmarks(self):
        """Test the main benchmark function that coordinates multiple scenarios."""
        scenarios = [
            {
                "name": "scenario1",
                "description": "Test scenario 1",
                "configs": [{"state_overrides": {"hope": 0.7}, "turns": 1}]
            },
            {
                "name": "scenario2",
                "description": "Test scenario 2",
                "configs": [{"state_overrides": {"hope": 0.3}, "turns": 1}]
            }
        ]
        
        with tempfile.TemporaryDirectory() as tmp_dir, \
             patch('scripts.run_causal_benchmarks.run_scenario_programmatically') as mock_run_scenario:
            
            # Mock the scenario runner
            mock_run_scenario.side_effect = [
                {"scenario": scenarios[0], "metrics": {"accuracy": {"overall": 0.8}}},
                {"scenario": scenarios[1], "metrics": {"accuracy": {"overall": 0.7}}}
            ]
            
            # Run the benchmarks
            output_file = "test_results.jsonl"
            run_causal_benchmarks(scenarios, tmp_dir, output_file)
            
            # Check calls
            assert mock_run_scenario.call_count == 2
            
            # Check that results file exists
            result_path = os.path.join(tmp_dir, output_file)
            assert os.path.exists(result_path)
            
            # Check summary file
            summary_path = os.path.join(tmp_dir, f"summary_{output_file}")
            assert os.path.exists(summary_path)
            
            # Verify summary content
            with open(summary_path, 'r') as f:
                summary = json.load(f)
                assert summary["total_scenarios"] == 2
                assert summary["successful_scenarios"] == 2
                assert len(summary["scenario_summaries"]) == 2