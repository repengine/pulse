import unittest
from Module_0000 import example_function

class TestModule0000(unittest.TestCase):
    def test_example_function(self):
        # This test assumes there is at least one .py file in the current directory
        count = example_function('.')
        self.assertGreaterEqual(count, 1)

if __name__ == "__main__":
    unittest.main()