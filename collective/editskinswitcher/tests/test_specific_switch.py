import unittest
import doctest

from Testing import ZopeTestCase as ztc
from collective.editskinswitcher.tests import base


def test_suite():
    return unittest.TestSuite([

        # Integration tests that use PloneTestCase
        ztc.ZopeDocFileSuite(
            'tests/specific_switch.txt', package='collective.editskinswitcher',
            test_class=base.BaseFunctionalTestCase),
        
        ])

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')