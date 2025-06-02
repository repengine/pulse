import unittest
from analytics.learning_profile import LearningProfile


class TestLearningProfile(unittest.TestCase):
    def test_from_dict(self):
        d = {
            "type": "statistical",
            "variable_stats": {"foo": {"suggested_weight": 1.0}},
        }
        profile = LearningProfile.from_dict(d)
        self.assertEqual(profile.type, "statistical")
        self.assertIn("foo", profile.variable_stats)

    def test_missing_fields(self):
        d = {"type": "causal"}
        profile = LearningProfile.from_dict(d)
        self.assertEqual(profile.type, "causal")
        self.assertEqual(profile.arc_performance, {})
        self.assertEqual(profile.tag_performance, {})

    def test_malformed_profile(self):
        d = {"notype": 123}
        with self.assertRaises(TypeError):
            LearningProfile.from_dict(d)


if __name__ == "__main__":
    unittest.main()
