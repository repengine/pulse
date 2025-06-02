"""
symbolic_overlay_demo.py

Demonstration of the enhanced symbolic overlay system showing the key improvements:
1. Isolation & gating between symbolic processing and retrodiction training
2. Performance optimizations with caching and lazy evaluation
3. Enhanced configurability with profiles and variable mappings
4. Dynamic overlay discovery and hierarchical relationships
5. Symbolic-numeric integration with bidirectional transforms

This script demonstrates a complete workflow using the improved symbolic overlay system.
"""

import os
import sys
import time

# Add parent directory to path to import Pulse modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.worldstate import WorldState
from symbolic_system.context import enter_retrodiction_mode, enter_simulation_mode
from symbolic_system.overlays import apply_overlay_interactions
from symbolic_system.config import get_symbolic_config
from symbolic_system.numeric_transforms import get_numeric_transformer
from symbolic_system.optimization import get_symbolic_cache


from typing import Optional


def print_divider(title: str) -> None:
    """Print a section divider"""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")


def print_overlays(state: WorldState, title: Optional[str] = None) -> None:
    """Pretty print the overlays"""
    if title:
        print(f"\n--- {title} ---")

    # Print primary overlays
    print("Primary overlays:")
    for name, value in state.overlays.get_primary_overlays().items():
        print(f"  {name:<10}: {value:.2f}")

    # Print secondary overlays if any
    secondary = state.overlays.get_secondary_overlays()
    if secondary:
        print("\nSecondary overlays:")
        for name, value in secondary.items():
            print(f"  {name:<10}: {value:.2f}")

    # Print dominant overlays
    dominant = state.overlays.get_dominant_overlays(threshold=0.65)
    if dominant:
        print("\nDominant overlays:")
        for name, value in dominant:
            print(f"  {name:<10}: {value:.2f}")
        print()


def demo_isolation_and_gating() -> None:
    """Demonstrate proper isolation between symbolic processing and retrodiction"""
    print_divider("1. Isolation & Gating Demonstration")

    # Create a state with some overlay values
    state = WorldState()
    state.overlays.hope = 0.7
    state.overlays.trust = 0.6

    print("Initial overlay values:")
    print(f"  hope: {state.overlays.hope:.2f}")
    print(f"  trust: {state.overlays.trust:.2f}")

    print("\nApplying overlay interactions in simulation mode (symbolic enabled):")
    with enter_simulation_mode(enable_symbolic=True):
        # Should apply interactions and change values
        apply_overlay_interactions(state)
        print(f"  hope: {state.overlays.hope:.2f}")
        print(
            f"  trust: {state.overlays.trust:.2f}"
        )  # Trust should increase due to high hope

    # Reset overlays for next test
    state.overlays.hope = 0.7
    state.overlays.trust = 0.6

    print("\nApplying overlay interactions in retrodiction mode (symbolic disabled):")
    with enter_retrodiction_mode(enable_symbolic=False):
        # Should not change values
        apply_overlay_interactions(state)
        print(f"  hope: {state.overlays.hope:.2f}")
        print(f"  trust: {state.overlays.trust:.2f}")  # Should remain unchanged

    print("\nEntering retrodiction mode with symbolic explicitly enabled:")
    with enter_retrodiction_mode(enable_symbolic=True):
        # Should apply minimal interactions
        apply_overlay_interactions(state)
        print(f"  hope: {state.overlays.hope:.2f}")
        print(f"  trust: {state.overlays.trust:.2f}")  # Should change slightly


def demo_performance_optimization() -> None:
    """Demonstrate performance optimizations with caching and lazy evaluation"""
    print_divider("2. Performance Optimization Demonstration")

    # Get the symbolic cache
    cache = get_symbolic_cache()
    cache.clear()  # Start with a clean cache

    transformer = get_numeric_transformer()

    print("Testing caching of numeric_to_symbolic transformations:")

    # First call - should compute and cache
    start_time = time.time()
    result1 = transformer.numeric_to_symbolic("volatility_index", 30)
    first_call_time = time.time() - start_time
    print(f"First call result: {result1}")
    print(f"Time taken: {first_call_time:.5f} seconds")

    # Second call with same parameters - should use cache
    start_time = time.time()
    result2 = transformer.numeric_to_symbolic("volatility_index", 30)
    second_call_time = time.time() - start_time
    print(f"Second call result: {result2}")
    print(f"Time taken: {second_call_time:.5f} seconds")

    # Should be faster using cache
    print(
        f"Speed improvement: {first_call_time / max(second_call_time, 0.0001):.1f}x faster"
    )

    print("\nCache statistics:")
    print(f"  Cache size: {len(cache.cache)} entries")
    print(
        f"  Hit rate: {cache.hits}/{cache.hits + cache.misses} "
        f"({cache.hits / (cache.hits + cache.misses) * 100:.1f}% if non-zero)"
    )


def demo_enhanced_configurability() -> None:
    """Demonstrate enhanced configurability with profiles"""
    print_divider("3. Enhanced Configurability Demonstration")

    # Get the configuration
    config = get_symbolic_config()

    print("Available profiles:")
    for profile in config.get_available_profiles():
        print(f"  - {profile}")

    # Show default profile settings
    config.set_active_profile("default")
    print("\nDefault profile settings:")
    print(f"  Dominance threshold: {config.get_value('overlay_thresholds.dominance')}")
    print(
        f"  Hope->Trust interaction: {config.get_value('interaction_strengths.hope->trust')}"
    )

    # Create a new profile
    print("\nCreating new 'bear_market' profile...")
    config.create_profile("bear_market", base_profile="high_volatility")
    config.set_active_profile("bear_market")
    config.set_value("overlay_thresholds.dominance", 0.8)
    config.set_value("interaction_strengths.despair->fatigue", 0.05)

    print("Bear market profile settings:")
    print(f"  Dominance threshold: {config.get_value('overlay_thresholds.dominance')}")
    print(
        f"  Despair->Fatigue interaction: {config.get_value('interaction_strengths.despair->fatigue')}"
    )

    # Auto-select profile based on market conditions
    print("\nAuto-selecting profile based on market conditions:")

    # Simulate bullish conditions
    bullish_variables = {
        "volatility_index": 12,
        "gdp_growth": 2.5,
        "unemployment_rate": 3.8,
    }
    selected_profile = config.auto_select_profile(bullish_variables)
    print(f"  For bullish market: selected '{selected_profile}' profile")

    # Simulate volatile conditions
    volatile_variables = {
        "volatility_index": 35,
        "gdp_growth": 1.0,
        "unemployment_rate": 4.5,
    }
    selected_profile = config.auto_select_profile(volatile_variables)
    print(f"  For volatile market: selected '{selected_profile}' profile")

    # Simulate recession conditions
    recession_variables = {
        "volatility_index": 40,
        "gdp_growth": -1.5,
        "unemployment_rate": 7.2,
    }
    selected_profile = config.auto_select_profile(recession_variables)
    print(f"  For recession: selected '{selected_profile}' profile")


def demo_overlay_sophistication() -> None:
    """Demonstrate dynamic overlay discovery and hierarchical relationships"""
    print_divider("4. Overlay Sophistication Demonstration")

    state = WorldState()

    print_overlays(state, "Initial state (default overlays only)")

    # Add some secondary overlays with hierarchical relationships
    print("Adding secondary overlays with hierarchical relationships...")

    # Children of hope
    state.overlays.add_overlay(
        name="optimism",
        value=0.6,
        category="secondary",
        parent="hope",
        description="Positive expectation about future",
    )

    state.overlays.add_overlay(
        name="confidence",
        value=0.7,
        category="secondary",
        parent="hope",
        description="Self-assurance about decisions",
    )

    # Children of despair
    state.overlays.add_overlay(
        name="anxiety",
        value=0.4,
        category="secondary",
        parent="despair",
        description="Worry about future outcomes",
    )

    state.overlays.add_overlay(
        name="uncertainty",
        value=0.5,
        category="secondary",
        parent="despair",
        description="Lack of conviction about direction",
    )

    # Child of rage
    state.overlays.add_overlay(
        name="frustration",
        value=0.6,
        category="secondary",
        parent="rage",
        description="Dissatisfaction with outcomes",
    )

    print_overlays(state, "After adding secondary overlays")

    # Show children of a parent overlay
    print("Children of 'hope':")
    for name, value in state.overlays.get_children("hope").items():
        metadata = state.overlays.get_metadata(name)
        description = metadata.description if metadata else ""
        print(f"  {name:<10}: {value:.2f} - {description}")

    # Set up relationships between overlays
    print("\nSetting relationships between overlays...")
    state.overlays.set_relationship(
        "optimism", "boosts", "confidence", 0.5
    )  # optimism boosts confidence
    state.overlays.set_relationship(
        "anxiety", "boosts", "uncertainty", 0.7
    )  # anxiety strongly boosts uncertainty
    state.overlays.set_relationship(
        "confidence", "reduces", "anxiety", -0.6
    )  # confidence reduces anxiety

    print("Relationship strengths:")
    print(
        f"  optimism → confidence: {state.overlays.get_relationship('optimism', 'confidence'):.2f}"
    )
    print(
        f"  anxiety → uncertainty: {state.overlays.get_relationship('anxiety', 'uncertainty'):.2f}"
    )
    print(
        f"  confidence → anxiety: {state.overlays.get_relationship('confidence', 'anxiety'):.2f}"
    )


def demo_symbolic_numeric_integration() -> None:
    """Demonstrate symbolic-numeric integration with bidirectional transforms"""
    print_divider("5. Symbolic-Numeric Integration Demonstration")

    state = WorldState()
    transformer = get_numeric_transformer()

    # Initialize with neutral overlay values
    state.overlays.hope = 0.5
    state.overlays.despair = 0.5
    state.overlays.rage = 0.5
    state.overlays.fatigue = 0.5
    state.overlays.trust = 0.5

    print_overlays(state, "Initial state with neutral values")

    # Create some market indicators
    print("\nSimulating current market indicators...")
    indicators = {
        "volatility_index": 35,  # High volatility
        "price_momentum": -3.2,  # Negative momentum
        "trading_volume": 1.5,  # Above average volume
        "rsi": 25,  # Oversold condition
    }

    print("Market indicators:")
    for name, value in indicators.items():
        print(f"  {name:<15}: {value}")

    # Transform indicators to symbolic overlays
    print("\nTransforming numeric indicators to symbolic overlays...")
    transformations = transformer.apply_numeric_to_state(state, indicators)

    print("Applied transformations:")
    for t in transformations:
        print(
            f"  {t['indicator']:<15} → {t['overlay']:<10}: {t['from_value']:.2f} → {t['to_value']:.2f} "
            f"(confidence: {t['confidence']:.2f})"
        )

    print_overlays(state, "After applying market indicators")

    # Show expected impacts of current emotional state on numeric variables
    print("\nExpected impacts of current emotional state on market variables:")

    # Check each primary overlay's impact
    for name, value in state.overlays.get_primary_overlays().items():
        impacts = transformer.symbolic_to_numeric(name, value)
        if impacts:
            print(f"\n  {name} ({value:.2f}) impacts:")
            for indicator, impact in impacts.items():
                print(f"    {indicator:<20}: {impact:+.2f}")


def full_demonstration() -> None:
    """Run a complete demonstration combining all improvements"""
    print_divider("COMPLETE DEMONSTRATION OF SYMBOLIC OVERLAY SYSTEM")

    # Create a world state with some initial values
    state = WorldState()
    state.overlays.hope = 0.6
    state.overlays.despair = 0.4

    # Set up configuration for different market regimes
    config = get_symbolic_config()
    transformer = get_numeric_transformer()

    # Add custom overlays for additional emotional nuance
    state.overlays.add_overlay(
        "concentration", 0.5, "secondary", "trust", "Focus on specific market segments"
    )
    state.overlays.add_overlay(
        "anticipation", 0.7, "secondary", "hope", "Expectation of upcoming catalysts"
    )

    print("Initial state:")
    print_overlays(state)

    # First scenario: Normal market (simulation mode)
    print("\n--- SCENARIO 1: NORMAL MARKET CONDITIONS ---")
    normal_indicators = {
        "volatility_index": 15,  # Normal volatility
        "price_momentum": 2.1,  # Moderate positive momentum
        "trading_volume": 1.0,  # Average volume
        "rsi": 55,  # Neutral RSI
    }

    # Use normal simulation mode with symbolic processing
    with enter_simulation_mode(enable_symbolic=True):
        # Auto-select appropriate profile
        config.auto_select_profile(normal_indicators)
        print(f"Selected profile: {config.get_active_profile()}")

        # Apply indicators to symbolic state
        transformer.apply_numeric_to_state(state, normal_indicators)

        # Apply overlay interactions based on current profile
        apply_overlay_interactions(state)

        print("State after normal market update:")
        print_overlays(state)

    # Second scenario: Market crash (high volatility)
    print("\n--- SCENARIO 2: MARKET CRASH (HIGH VOLATILITY) ---")
    crash_indicators = {
        "volatility_index": 45,  # Very high volatility
        "price_momentum": -8.5,  # Strong negative momentum
        "trading_volume": 3.2,  # Very high volume (panic selling)
        "rsi": 15,  # Extremely oversold
    }

    with enter_simulation_mode(enable_symbolic=True):
        # Auto-select appropriate profile for crash
        config.auto_select_profile(crash_indicators)
        print(f"Selected profile: {config.get_active_profile()}")

        # Apply crash indicators
        transformer.apply_numeric_to_state(state, crash_indicators)

        # Apply overlay interactions
        apply_overlay_interactions(state)

        print("State after market crash:")
        print_overlays(state)

        # Get impacts on numeric variables from current emotional state
        print("\nExpected market impacts from current emotional state:")
        for name, value in state.overlays.get_primary_overlays().items():
            if value > 0.6:  # Only show dominant overlays
                impacts = transformer.symbolic_to_numeric(name, value)
                if impacts:
                    print(f"  {name} ({value:.2f}) predicts:")
                    for indicator, impact in impacts.items():
                        print(f"    {indicator:<20}: {impact:+.2f}")

    # Third scenario: Retrodiction training (symbolic disabled)
    print("\n--- SCENARIO 3: RETRODICTION TRAINING (SYMBOLIC DISABLED) ---")

    # Save original values to verify no changes
    original_hope = state.overlays.hope
    original_despair = state.overlays.despair

    with enter_retrodiction_mode(enable_symbolic=False):
        # These operations should be no-ops in retrodiction mode
        apply_overlay_interactions(state)
        transformer.apply_numeric_to_state(state, crash_indicators)

        print("State after retrodiction mode operations:")
        print_overlays(state)

        # Verify values didn't change
        if (
            state.overlays.hope == original_hope
            and state.overlays.despair == original_despair
        ):
            print(
                "\nConfirmed: Symbolic operations properly isolated during retrodiction!"
            )
        else:
            print("\nWarning: Symbolic values changed during retrodiction mode!")


if __name__ == "__main__":
    # Uncomment individual demos as needed
    demo_isolation_and_gating()
    demo_performance_optimization()
    demo_enhanced_configurability()
    demo_overlay_sophistication()
    demo_symbolic_numeric_integration()

    # Uncomment for the full demonstration
    # full_demonstration()
