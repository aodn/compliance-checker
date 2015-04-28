#!/usr/bin/env python

from compliance_checker.imos import IMOSCheck
from compliance_checker.cf.util import is_vertical_coordinate, is_time_variable, units_convertible
from compliance_checker.base import DSPair
from wicken.netcdf_dogma import NetCDFDogma
from netCDF4 import Dataset
from tempfile import gettempdir
from pkg_resources import resource_filename

import unittest
import os
import re


static_files = {
        'bad_data' : resource_filename('compliance_checker', 'tests/data/imos_bad_missing_data.nc'),
        'good_data' : resource_filename('compliance_checker', 'tests/data/imos_good_data.nc')
        }

class TestIMOS(unittest.TestCase):
    # @see
    # http://www.saltycrane.com/blog/2012/07/how-prevent-nose-unittest-using-docstring-when-verbosity-2/
    def shortDescription(self):
        return None

    # override __str__ and __repr__ behavior to show a copy-pastable nosetest name for ion tests
    #  ion.module:TestClassName.test_function_name
    def __repr__(self):
        name = self.id()
        name = name.split('.')
        if name[0] not in ["ion", "pyon"]:
            return "%s (%s)" % (name[-1], '.'.join(name[:-1]))
        else:
            return "%s ( %s )" % (name[-1], '.'.join(name[:-2]) + ":" + '.'.join(name[-2:]))
    __str__ = __repr__

    def setUp(self):
        '''
        Initialize the dataset
        '''
        self.imos = IMOSCheck()
        self.good_dataset = self.get_pair(static_files['good_data'])
        self.bad_dataset = self.get_pair(static_files['bad_data'])

    def get_pair(self, nc_dataset):
        '''
        Return a pairwise object for the dataset
        '''
        if isinstance(nc_dataset, basestring):
            nc_dataset = Dataset(nc_dataset, 'r')
            self.addCleanup(nc_dataset.close)

        dogma = NetCDFDogma('nc', self.imos.beliefs(), nc_dataset)
        pair = DSPair(nc_dataset, dogma)
        return pair

    #--------------------------------------------------------------------------------
    # Compliance Tests
    #--------------------------------------------------------------------------------

    def test_check_global_attributes(self):
        ret_val = self.imos.check_global_attributes(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_global_attributes(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

    def test_check_variable_attributes(self):

        ret_val = self.imos.check_variable_attributes(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_variable_attributes(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)
        
        