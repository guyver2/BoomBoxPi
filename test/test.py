import unittest

class TestStringMethodsDummy(unittest.TestCase):

    def test_dummy_pass(self):
        self.assertEqual(1,1)
    
    def test_dummy_fail(self):
        self.assertEqual(1,0)

if __name__ == '__main__':
    unittest.main()
