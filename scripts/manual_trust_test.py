import logging
from analytics.bayesian_trust_tracker import bayesian_trust_tracker
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_manual_trust_test():
    entity_id = "test_entity_manual"
    initial_trust = bayesian_trust_tracker.get_trust(entity_id)
    logger.info(f"Initial trust for {entity_id}: {initial_trust}")

    # Simulate a series of outcomes
    outcomes = [True, True, False, True, True]  # Predominantly positive
    logger.info(f"Simulating outcomes: {outcomes}")

    for i, outcome in enumerate(outcomes):
        bayesian_trust_tracker.update(entity_id, outcome)
        current_trust = bayesian_trust_tracker.get_trust(entity_id)
        confidence_interval = bayesian_trust_tracker.get_confidence_interval(entity_id)
        logger.info(
            f"After outcome {i + 1} ({outcome}): "
            f"Trust={current_trust:.4f}, "
            f"95% CI=({confidence_interval[0]:.4f}, {confidence_interval[1]:.4f})"
        )

    final_trust = bayesian_trust_tracker.get_trust(entity_id)
    logger.info(f"Final trust for {entity_id}: {final_trust}")

    if final_trust > initial_trust:
        logger.info(
            f"SUCCESS: Trust for {entity_id} increased from {
                initial_trust:.4f} to {
                final_trust:.4f} after positive outcomes.")
    elif final_trust < initial_trust:
        logger.warning(
            f"UNEXPECTED: Trust for {entity_id} decreased from {
                initial_trust:.4f} to {
                final_trust:.4f} despite predominantly positive outcomes.")
    else:
        logger.warning(
            f"UNEXPECTED: Trust for {entity_id} remained unchanged at {
                initial_trust:.4f} despite updates.")

    # Test with a different entity and predominantly negative outcomes
    entity_id_neg = "test_entity_manual_neg"
    initial_trust_neg = bayesian_trust_tracker.get_trust(entity_id_neg)
    logger.info(f"\nInitial trust for {entity_id_neg}: {initial_trust_neg}")

    outcomes_neg = [False, False, True, False, False]  # Predominantly negative
    logger.info(f"Simulating outcomes for {entity_id_neg}: {outcomes_neg}")

    for i, outcome in enumerate(outcomes_neg):
        bayesian_trust_tracker.update(entity_id_neg, outcome)
        current_trust_neg = bayesian_trust_tracker.get_trust(entity_id_neg)
        confidence_interval_neg = bayesian_trust_tracker.get_confidence_interval(
            entity_id_neg
        )
        logger.info(
            f"After outcome {
                i +
                1} ({outcome}) for {entity_id_neg}: " f"Trust={
                current_trust_neg:.4f}, " f"95% CI=({
                confidence_interval_neg[0]:.4f}, {
                    confidence_interval_neg[1]:.4f})")

    final_trust_neg = bayesian_trust_tracker.get_trust(entity_id_neg)
    logger.info(f"Final trust for {entity_id_neg}: {final_trust_neg}")

    if final_trust_neg < initial_trust_neg:
        logger.info(
            f"SUCCESS: Trust for {entity_id_neg} decreased from {
                initial_trust_neg:.4f} to {
                final_trust_neg:.4f} after negative outcomes.")
    elif final_trust_neg > initial_trust_neg:
        logger.warning(
            f"UNEXPECTED: Trust for {entity_id_neg} increased from {
                initial_trust_neg:.4f} to {
                final_trust_neg:.4f} despite predominantly negative outcomes.")
    else:
        logger.warning(
            f"UNEXPECTED: Trust for {entity_id_neg} remained unchanged at {
                initial_trust_neg:.4f} despite updates.")


if __name__ == "__main__":
    run_manual_trust_test()
