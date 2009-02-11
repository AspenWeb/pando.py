import os
import unittest

class GeneratorMethodHaver:
    def gen(self):
        def test():
            assert 1 == 1
        yield (test,)


class TestIssue202(unittest.TestCase):

    def test_generator_function(self):
        from nose.loader import TestLoader

        def setup():    pass
        def teardown(): pass
        def gen():
            def test():
                assert 1 == 1
            yield (test,)
        gen.setup = setup
        gen.teardown = teardown

        loader = TestLoader()
        suite = loader.loadTestsFromGenerator(gen, module=None)
        testcase = iter(suite).next()
        self.assertEqual(testcase.test.setUpFunc, setup)
        self.assertEqual(testcase.test.tearDownFunc, teardown)


if __name__ == '__main__':
    unittest.main()
