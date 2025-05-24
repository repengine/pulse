"""
CostController

Central service for monitoring and limiting API and token usage costs.
Tracks costs across the Recursive Training System and enforces limits
to prevent exceeding budget thresholds.
"""

import logging
import threading
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Dict, Optional

# Import recursive training components
from recursive_training.metrics.metrics_store import get_metrics_store


class CostStatus(Enum):
    """Status levels for cost tracking."""

    OK = "ok"
    WARNING = "warning"
    CRITICAL = "critical"
    SHUTDOWN = "shutdown"


class CostLimitException(Exception):
    """Exception raised when a cost limit is exceeded."""

    def __init__(self, message, current_cost, limit):
        self.message = message
        self.current_cost = current_cost
        self.limit = limit
        super().__init__(self.message)


class CostController:
    """
    Central cost monitoring and limiting service.

    Features:
    - Track API call costs across the system
    - Enforce daily, monthly, and total cost limits
    - Provide rate limiting for API calls
    - Offer cost estimation for planned operations
    - Generate cost reports and forecasts
    - Trigger alerts and shutdowns when thresholds are exceeded
    """

    # Singleton instance
    _instance = None

    @classmethod
    def get_instance(cls, config: Optional[Dict[str, Any]] = None) -> "CostController":
        """
        Get or create the singleton instance of CostController.

        Args:
            config: Optional configuration dictionary

        Returns:
            CostController instance
        """
        if cls._instance is None:
            cls._instance = CostController(config)
        return cls._instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CostController.

        Args:
            config: Optional configuration dictionary
        """
        self.logger = logging.getLogger("CostController")
        self.config = config or {}

        # Initialize metrics store
        self.metrics_store = get_metrics_store()

        # Configure cost limits
        self.daily_limit = self.config.get("daily_cost_limit_usd", 10.0)
        self.monthly_limit = self.config.get("monthly_cost_limit_usd", 100.0)
        self.total_limit = self.config.get("total_cost_limit_usd", 1000.0)

        # Configure threshold percentages
        self.warning_threshold = self.config.get("warning_threshold_percentage", 70)
        self.critical_threshold = self.config.get("critical_threshold_percentage", 90)

        # Configure rate limits
        self.rate_limits = {
            "per_minute": self.config.get("max_calls_per_minute", 60),
            "per_hour": self.config.get("max_calls_per_hour", 500),
            "per_day": self.config.get("max_calls_per_day", 5000),
        }

        # Initialize tracking variables
        self.current_day_cost = 0.0
        self.current_month_cost = 0.0
        self.total_cost = 0.0

        self.api_calls = {"daily": 0, "monthly": 0, "total": 0}

        self.token_usage = {"daily": 0, "monthly": 0, "total": 0}

        # Initialize rate limiting tracking
        self.call_timestamps = []
        self.call_history_lock = threading.Lock()

        # Initialize status
        self.current_status = CostStatus.OK

        # Initialize day and month tracking
        self.current_day = datetime.now(timezone.utc).date()
        self.current_month = (self.current_day.year, self.current_day.month)

        # Load historical data
        self._load_historical_data()

        self.logger.info("CostController initialized")

    def _load_historical_data(self):
        """Load historical cost data from metrics store."""
        try:
            # Query for cost metrics
            today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            month_start = datetime.now(timezone.utc).replace(day=1).strftime("%Y-%m-%d")

            # Get today's costs
            daily_metrics = self.metrics_store.query_metrics(
                metric_types=["cost"], start_date=today_str
            )

            # Sum up daily costs
            for metric in daily_metrics:
                self.current_day_cost += metric.get("cost", 0.0)
                self.api_calls["daily"] += metric.get("api_calls", 0)
                self.token_usage["daily"] += metric.get("token_usage", 0)

            # Get month's costs
            monthly_metrics = self.metrics_store.query_metrics(
                metric_types=["cost"], start_date=month_start
            )

            # Sum up monthly costs
            for metric in monthly_metrics:
                self.current_month_cost += metric.get("cost", 0.0)
                self.api_calls["monthly"] += metric.get("api_calls", 0)
                self.token_usage["monthly"] += metric.get("token_usage", 0)

            # Get all-time costs from summary
            summary = self.metrics_store.get_metrics_summary()
            self.total_cost = summary["cost_tracking"]["total_cost"]
            self.api_calls["total"] = summary["cost_tracking"]["api_calls"]
            self.token_usage["total"] = summary["cost_tracking"]["token_usage"]

            # Update status based on loaded data
            self._update_status()

            self.logger.info(
                f"Loaded historical cost data: daily=${self.current_day_cost:.2f}, "
                f"monthly=${self.current_month_cost:.2f}, total=${self.total_cost:.2f}"
            )
        except Exception as e:
            self.logger.error(f"Error loading historical cost data: {e}")

    def _update_status(self):
        """Update cost status based on current costs and limits."""
        daily_percentage = (
            (self.current_day_cost / self.daily_limit) * 100
            if self.daily_limit > 0
            else 0
        )
        monthly_percentage = (
            (self.current_month_cost / self.monthly_limit) * 100
            if self.monthly_limit > 0
            else 0
        )

        if daily_percentage >= 100 or monthly_percentage >= 100:
            self.current_status = CostStatus.SHUTDOWN
        elif (
            daily_percentage >= self.critical_threshold
            or monthly_percentage >= self.critical_threshold
        ):
            self.current_status = CostStatus.CRITICAL
        elif (
            daily_percentage >= self.warning_threshold
            or monthly_percentage >= self.warning_threshold
        ):
            self.current_status = CostStatus.WARNING
        else:
            self.current_status = CostStatus.OK

    def _check_day_change(self):
        """Check if the day has changed and reset daily counters if needed."""
        current_date = datetime.now(timezone.utc).date()
        if current_date != self.current_day:
            self.logger.info(f"Day changed from {self.current_day} to {current_date}")
            self.current_day = current_date
            self.current_day_cost = 0.0
            self.api_calls["daily"] = 0
            self.token_usage["daily"] = 0
            self.call_timestamps = []

            # Also check for month change
            current_month = (current_date.year, current_date.month)
            if current_month != self.current_month:
                self.logger.info(
                    f"Month changed from {self.current_month} to {current_month}"
                )
                self.current_month = current_month
                self.current_month_cost = 0.0
                self.api_calls["monthly"] = 0
                self.token_usage["monthly"] = 0

    def _check_rate_limits(self):
        """
        Check if current API call rate exceeds limits.

        Returns:
            True if within limits, False if exceeding limits
        """
        with self.call_history_lock:
            # Clean up old timestamps
            now = datetime.now(timezone.utc)
            day_ago = now - timedelta(days=1)
            self.call_timestamps = [ts for ts in self.call_timestamps if ts > day_ago]

            # Check per-minute limit
            minute_ago = now - timedelta(minutes=1)
            minute_count = sum(1 for ts in self.call_timestamps if ts > minute_ago)
            if minute_count >= self.rate_limits["per_minute"]:
                return False

            # Check per-hour limit
            hour_ago = now - timedelta(hours=1)
            hour_count = sum(1 for ts in self.call_timestamps if ts > hour_ago)
            if hour_count >= self.rate_limits["per_hour"]:
                return False

            # Check per-day limit
            day_count = len(self.call_timestamps)
            if day_count >= self.rate_limits["per_day"]:
                return False

            return True

    def track_cost(
        self,
        api_calls: int = 0,
        token_usage: int = 0,
        direct_cost: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Track API usage cost.

        Args:
            api_calls: Number of API calls made
            token_usage: Number of tokens used
            direct_cost: Direct cost in USD (if provided, token-based estimation is skipped)

        Returns:
            Cost tracking information
        """
        # Check for day/month changes
        self._check_day_change()

        # Calculate cost if not provided directly
        cost = direct_cost
        if cost is None and token_usage > 0:
            # Basic cost estimation (adjust based on your specific API costs)
            cost = token_usage * 0.000002  # $0.002 per 1000 tokens

        # If we still don't have a cost but have API calls, estimate based on calls
        if cost is None and api_calls > 0:
            cost = api_calls * 0.001  # $0.001 per API call

        # Default to zero if still None
        cost = cost or 0.0

        # Update tracking
        self.current_day_cost += cost
        self.current_month_cost += cost
        self.total_cost += cost

        self.api_calls["daily"] += api_calls
        self.api_calls["monthly"] += api_calls
        self.api_calls["total"] += api_calls

        self.token_usage["daily"] += token_usage
        self.token_usage["monthly"] += token_usage
        self.token_usage["total"] += token_usage

        # Add timestamp for rate limiting
        with self.call_history_lock:
            if api_calls > 0:
                now = datetime.now(timezone.utc)
                self.call_timestamps.extend([now] * api_calls)

        # Update status
        self._update_status()

        # Track in metrics store
        _timestamp = datetime.now(timezone.utc).isoformat()
        self.metrics_store.track_cost(cost, api_calls, token_usage)

        # Return tracking information
        return {
            "cost_usd": cost,
            "api_calls": api_calls,
            "token_usage": token_usage,
            "daily_cost_usd": self.current_day_cost,
            "monthly_cost_usd": self.current_month_cost,
            "total_cost_usd": self.total_cost,
            "status": self.current_status.value,
            "daily_limit_percentage": (self.current_day_cost / self.daily_limit) * 100
            if self.daily_limit > 0
            else 0,
            "monthly_limit_percentage": (self.current_month_cost / self.monthly_limit)
            * 100
            if self.monthly_limit > 0
            else 0,
        }

    def track_operation(
        self,
        operation_type: str,
        data_size: int = 0,
        duration: float = 0.0,
        cost: float = 0.0,
    ):
        """
        Track a specific operation for cost and resource usage.

        Args:
            operation_type: Type of operation (e.g., "model_inference", "data_processing")
            data_size: Size of data processed (optional)
            duration: Duration of the operation in seconds (optional)
            cost: Direct cost of the operation (optional)
        """
        # Placeholder implementation - actual tracking logic goes here
        self.logger.debug(
            f"Tracking operation: {operation_type}, data_size: {data_size}, duration: {duration}, cost: {cost}"
        )
        # In a real implementation, this would update internal metrics and potentially store in metrics_store

    def check_cost_limit(self, estimated_cost: float = 0.0) -> bool:
        """
        Check if an operation would exceed cost limits.

        Args:
            estimated_cost: Estimated cost of the operation

        Returns:
            True if within limits, False if would exceed limits

        Raises:
            CostLimitException: If operation would exceed daily, monthly, or total limit
        """
        # Check day/month changes
        self._check_day_change()

        # Check daily limit
        new_daily_cost = self.current_day_cost + estimated_cost
        if new_daily_cost > self.daily_limit:
            raise CostLimitException(
                f"Operation would exceed daily cost limit (${new_daily_cost:.2f} > ${self.daily_limit:.2f})",
                new_daily_cost,
                self.daily_limit,
            )

        # Check monthly limit
        new_monthly_cost = self.current_month_cost + estimated_cost
        if new_monthly_cost > self.monthly_limit:
            raise CostLimitException(
                f"Operation would exceed monthly cost limit (${new_monthly_cost:.2f} > ${self.monthly_limit:.2f})",
                new_monthly_cost,
                self.monthly_limit,
            )

        # Check total limit
        new_total_cost = self.total_cost + estimated_cost
        if new_total_cost > self.total_limit:
            raise CostLimitException(
                f"Operation would exceed total cost limit (${new_total_cost:.2f} > ${self.total_limit:.2f})",
                new_total_cost,
                self.total_limit,
            )

        return True

    def can_make_api_call(
        self, count: int = 1, token_estimate: int = 0, check_cost: bool = True
    ) -> bool:
        """
        Check if API calls can be made within rate and cost limits.

        Args:
            count: Number of API calls to check
            token_estimate: Estimated token usage
            check_cost: Whether to check cost limits

        Returns:
            True if calls can be made, False otherwise
        """
        # First check rate limits
        if not self._check_rate_limits():
            self.logger.warning("API call rejected due to rate limit")
            return False

        # Then check cost limits if requested
        if check_cost:
            # Estimate cost
            estimated_cost = (token_estimate * 0.000002) or (count * 0.001)

            try:
                self.check_cost_limit(estimated_cost)
            except CostLimitException as e:
                self.logger.warning(f"API call rejected due to cost limit: {e}")
                return False

        # Also reject if in SHUTDOWN status
        if self.current_status == CostStatus.SHUTDOWN:
            self.logger.warning("API call rejected due to SHUTDOWN status")
            return False

        return True

    def get_cost_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current cost tracking.

        Returns:
            Dictionary with cost summary information
        """
        # Check for day/month changes first
        self._check_day_change()

        # Calculate limit percentages
        daily_percentage = (
            (self.current_day_cost / self.daily_limit) * 100
            if self.daily_limit > 0
            else 0
        )
        monthly_percentage = (
            (self.current_month_cost / self.monthly_limit) * 100
            if self.monthly_limit > 0
            else 0
        )
        total_percentage = (
            (self.total_cost / self.total_limit) * 100 if self.total_limit > 0 else 0
        )

        return {
            "current_status": self.current_status.value,
            "daily": {
                "cost_usd": self.current_day_cost,
                "limit_usd": self.daily_limit,
                "percentage": daily_percentage,
                "api_calls": self.api_calls["daily"],
                "token_usage": self.token_usage["daily"],
            },
            "monthly": {
                "cost_usd": self.current_month_cost,
                "limit_usd": self.monthly_limit,
                "percentage": monthly_percentage,
                "api_calls": self.api_calls["monthly"],
                "token_usage": self.token_usage["monthly"],
            },
            "total": {
                "cost_usd": self.total_cost,
                "limit_usd": self.total_limit,
                "percentage": total_percentage,
                "api_calls": self.api_calls["total"],
                "token_usage": self.token_usage["total"],
            },
            "rate_limits": self.rate_limits,
            "thresholds": {
                "warning": self.warning_threshold,
                "critical": self.critical_threshold,
            },
            "current_day": self.current_day.isoformat(),
            "current_month": f"{self.current_month[0]}-{self.current_month[1]:02d}",
        }

    def get_cost_forecast(self, days_ahead: int = 30) -> Dict[str, Any]:
        """
        Generate a cost forecast based on current usage patterns.

        Args:
            days_ahead: Number of days to forecast

        Returns:
            Dictionary with forecast information
        """
        # Get historical daily average (last 7 days)
        week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        recent_metrics = self.metrics_store.query_metrics(
            metric_types=["cost"], start_date=week_ago, end_date=today
        )

        # Organize by day
        daily_costs = {}
        for metric in recent_metrics:
            timestamp = metric.get("timestamp", "")
            date_part = timestamp.split("T")[0] if "T" in timestamp else timestamp

            if date_part not in daily_costs:
                daily_costs[date_part] = 0.0

            daily_costs[date_part] += metric.get("cost", 0.0)

        # Calculate daily average
        if daily_costs:
            daily_average = sum(daily_costs.values()) / len(daily_costs)
        else:
            # If no historical data, use current day's cost
            daily_average = self.current_day_cost

        # Generate forecast
        forecast = {
            "daily_average_usd": daily_average,
            "forecast_days": days_ahead,
            "projected_cost_usd": daily_average * days_ahead,
            "projected_monthly_usd": daily_average * 30,  # 30-day month
            "projected_annual_usd": daily_average * 365,
            "days_until_daily_limit": (self.daily_limit / daily_average)
            if daily_average > 0
            else float("inf"),
            "days_until_monthly_limit": (
                (self.monthly_limit - self.current_month_cost) / daily_average
            )
            if daily_average > 0
            else float("inf"),
            "days_until_total_limit": (
                (self.total_limit - self.total_cost) / daily_average
            )
            if daily_average > 0
            else float("inf"),
        }

        return forecast


def get_cost_controller(config: Optional[Dict[str, Any]] = None) -> CostController:
    """
    Get the singleton instance of CostController.

    Args:
        config: Optional configuration dictionary

    Returns:
        CostController instance
    """
    return CostController.get_instance(config)
