#!/usr/bin/env python

import unittest
import os
import re

from wicken.netcdf_dogma import NetCDFDogma
from netCDF4 import Dataset
from tempfile import gettempdir
from pkg_resources import resource_filename

from compliance_checker.imos import IMOSFileNameCheck 
from compliance_checker.base import DSPair

static_files = {
    'file_name': resource_filename('compliance_checker', 'tests/data/imos_file_name.nc'),
}


class TestIMOSFileName(unittest.TestCase):
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
        self.check = IMOSFileNameCheck()
        self._good_dataset = self.get_pair(static_files['file_name'])
        self._good_dataset.ds_loc = 'IMOS_SRS-A_RFK_2014-09-07T06:39:47Z_ITFTIS_FV01_CDOM_END-20110821T035100Z_C-20140401T110000Z_PART10.nc'

        self._bad_dataset = self.get_pair(static_files['file_name'])
        self._bad_dataset.ds_loc = 'part1_part2_ABD_ab_abc.abc'

        self._bad_field7_to_field10_dataset = self.get_pair(static_files['file_name'])
        self._bad_field7_to_field10_dataset.ds_loc = 'part1_part2_ABD_ab_ab_ab_123_ab_ab_10.abc'

    def get_pair(self, nc_dataset_loc):
        '''
        Return a pairwise object for the dataset
        '''

        if isinstance(nc_dataset_loc, basestring):
            nc_dataset = Dataset(nc_dataset_loc, 'r')
            self.addCleanup(nc_dataset.close)
        dogma = NetCDFDogma('nc', self.check.beliefs(), nc_dataset)

        pair = DSPair(nc_dataset, dogma, ds_loc=nc_dataset_loc)
        return pair

    #--------------------------------------------------------------------------------
    # Compliance Tests
    #--------------------------------------------------------------------------------

    def test_check_extension_name(self):
        self.check.setup(self._good_dataset)

        ret_val = self.check.check_extension_name(self._good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)


        self.check.setup(self._bad_dataset)

        ret_val = self.check.check_extension_name(self._bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_file_name(self):
        self.check.setup(self._good_dataset)

        ret_val = self.check.check_file_name(self._good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)


        self.check.setup(self._bad_dataset)

        ret_val = self.check.check_file_name(self._bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_file_name_field1(self):
        self.check.setup(self._good_dataset)

        ret_val = self.check.check_file_name_field1(self._good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)


        self.check.setup(self._bad_dataset)

        ret_val = self.check.check_file_name_field1(self._bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_file_name_field2(self):
        self.check.setup(self._good_dataset)

        ret_val = self.check.check_file_name_field2(self._good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)


        self.check.setup(self._bad_dataset)

        ret_val = self.check.check_file_name_field2(self._bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_file_name_field3(self):
        self.check.setup(self._good_dataset)

        ret_val = self.check.check_file_name_field3(self._good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        self.check.setup(self._bad_dataset)

        ret_val = self.check.check_file_name_field3(self._bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_file_name_field5(self):
        self.check.setup(self._good_dataset)

        ret_val = self.check.check_file_name_field5(self._good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        self.check.setup(self._bad_dataset)

        ret_val = self.check.check_file_name_field5(self._bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_file_name_field6(self):
        self.check.setup(self._good_dataset)

        ret_val = self.check.check_file_name_field6(self._good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        self.check.setup(self._bad_dataset)

        ret_val = self.check.check_file_name_field6(self._bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_file_name_field4(self):
        self.check.setup(self._good_dataset)

        ret_val = self.check.check_file_name_field4(self._good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        self.check.setup(self._bad_dataset)

        ret_val = self.check.check_file_name_field4(self._bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_file_name_field7_to_field10(self):
        self.check.setup(self._good_dataset)

        ret_val = self.check.check_file_name_field7_to_field10(self._good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        self.check.setup(self._bad_field7_to_field10_dataset)

        ret_val = self.check.check_file_name_field7_to_field10(self._bad_field7_to_field10_dataset)

        for result in ret_val:
            self.assertFalse(result.value)
