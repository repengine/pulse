import unittest
import pandas as pd
from learning.transforms.rolling_features import rolling_mean_feature


class TestRollingFeatures(unittest.TestCase):
    def test_rolling_mean_feature_basic(self):
        df = pd.DataFrame({"value": [1, 2, 3, 4, 5]})
        result = rolling_mean_feature(df, window=3)
        expected = pd.Series([1.0, 1.5, 2.0, 3.0, 4.0], name="value_rolling_mean_3")
        pd.testing.assert_series_equal(result.reset_index(drop=True), expected)

    def test_rolling_mean_feature_column_arg(self):
        df = pd.DataFrame({"a": [10, 20, 30], "b": [1, 2, 3]})
        result = rolling_mean_feature(df, window=2, column="b")
        expected = pd.Series([1.0, 1.5, 2.5], name="b_rolling_mean_2")
        pd.testing.assert_series_equal(result.reset_index(drop=True), expected)


if __name__ == "__main__":
    unittest.main()
