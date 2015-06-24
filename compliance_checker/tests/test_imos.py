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
        'bad_data' : resource_filename('compliance_checker', 'tests/data/imos_bad_data.nc'),
        'good_data' : resource_filename('compliance_checker', 'tests/data/imos_good_data.nc'),
        'missing_data' : resource_filename('compliance_checker', 'tests/data/imos_missing_data.nc'),
        'test_variable' : resource_filename('compliance_checker', 'tests/data/imos_variable_test.nc'),
        'data_var' : resource_filename('compliance_checker', 'tests/data/imos_data_var.nc'),
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
        self.missing_dataset = self.get_pair(static_files['missing_data'])
        self.test_variable_dataset = self.get_pair(static_files['test_variable'])
        self.data_variable_dataset = self.get_pair(static_files['data_var'])

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

    def test_check_project_attribute(self):
        ret_val = self.imos.check_project_attribute(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_project_attribute(self.bad_dataset)
        
        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_conventions_attribute(self):
        ret_val = self.imos.check_conventions(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_conventions(self.bad_dataset)
        
        for result in ret_val:
            self.assertFalse(result.value)
    
    def test_check_naming_authority(self):
        ret_val = self.imos.check_naming_authority(self.good_dataset)
        
        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_naming_authority(self.bad_dataset)
        
        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_data_centre(self):
        ret_val = self.imos.check_data_centre(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_data_centre(self.bad_dataset)
        
        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_author(self):
        ret_val = self.imos.check_author(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_author(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_geospatial_lat_min_max(self):
        ret_val = self.imos.check_geospatial_lat_min_max(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_geospatial_lat_min_max(self.bad_dataset)

        for result in ret_val:
            if 'check_attribute_type' in result.name:
                self.assertTrue(result.value)
            else:
                self.assertFalse(result.value)

        ret_val = self.imos.check_geospatial_lat_min_max(self.missing_dataset)

        self.assertTrue(len(ret_val) == 0)

    def test_check_geospatial_lon_min_max(self):
        ret_val = self.imos.check_geospatial_lat_min_max(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_geospatial_lat_min_max(self.bad_dataset)

        for result in ret_val:
            if 'check_attribute_type' in result.name:
                self.assertTrue(result.value)
            else:
                self.assertFalse(result.value)

        ret_val = self.imos.check_geospatial_lat_min_max(self.missing_dataset)

        self.assertTrue(len(ret_val) == 0)

    def test_check_geospatial_vertical_min_max(self):
        ret_val = self.imos.check_geospatial_vertical_min_max(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_geospatial_vertical_min_max(self.bad_dataset)

        for result in ret_val:
            if 'check_attribute_type' in result.name:
                self.assertTrue(result.value)
            else:
                self.assertFalse(result.value)

        ret_val = self.imos.check_geospatial_vertical_min_max(self.missing_dataset)

        self.assertTrue(len(ret_val) == 0)

    def test_check_time_coverage(self):
        ret_val = self.imos.check_time_coverage(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_time_coverage(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_time_coverage(self.missing_dataset)

        self.assertTrue(len(ret_val) == 0)

    def test_check_title(self):
        ret_val = self.imos.check_title(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_title(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_title(self.missing_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_date_created(self):
        ret_val = self.imos.check_date_created(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_date_created(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)


    def test_check_abstract(self):

        ret_val = self.imos.check_abstract(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_abstract(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_abstract(self.missing_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_data_centre_email(self):
        ret_val = self.imos.check_data_centre_email(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_data_centre_email(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_data_centre_email(self.missing_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_principal_investigator(self):
        ret_val = self.imos.check_principal_investigator(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_principal_investigator(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_principal_investigator(self.missing_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_citation(self):
        ret_val = self.imos.check_citation(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_citation(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_citation(self.missing_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_variables_long_name(self):
        ret_val = self.imos.check_variables_long_name(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_variables_long_name(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_variables_long_name(self.missing_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_check_coordinate_variables(self):
        self.imos.setup(self.good_dataset)

        self.assertTrue(len(self.imos._coordinate_variables) == 1)

        ret_val = self.imos.check_coordinate_variables(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

    def test_check_time_variable(self):
        ret_val = self.imos.check_time_variable(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_time_variable(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_time_variable(self.missing_dataset)

        self.assertTrue(len(ret_val) == 0)

    def test_check_longitude_variable(self):
        ret_val = self.imos.check_longitude_variable(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_longitude_variable(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_longitude_variable(self.missing_dataset)

        self.assertTrue(len(ret_val) == 0)

    def test_check_latitude_variable(self):
        ret_val = self.imos.check_latitude_variable(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_latitude_variable(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_latitude_variable(self.missing_dataset)
        
        self.assertTrue(len(ret_val) == 0)
    
    def test_check_vertical_variable(self):
        ret_val = self.imos.check_vertical_variable(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_vertical_variable(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_vertical_variable(self.missing_dataset)
        
        self.assertTrue(len(ret_val) == 0)

    def test_check_variable_attribute_type(self):
        ret_val = self.imos.check_variable_attribute_type(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_variable_attribute_type(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

    def test_data_variable_list(self):
        self.imos.setup(self.data_variable_dataset)
        self.assertEqual(len(self.imos._data_variables), 2)
        self.assertEqual(self.imos._data_variables[0].name, 'data_variable')
        self.assertEqual(self.imos._data_variables[1].name, 'random_data')

    def test_check_data_variables(self):
        self.imos.setup(self.good_dataset)
        ret_val = self.imos.check_data_variables(self.good_dataset)

        for result in ret_val:
            if 'check_dimension' in result.name:
                if'LATITUDE' in result.name or 'LONGITUDE' in result.name or 'NOMINAL_DEPTH' in result.name:
                    self.assertFalse(result.value)
                else:
                    self.assertTrue(result.value)
            else:
                self.assertTrue(result.value)

    def test_check_quality_variable_dimensions(self):
        self.imos.setup(self.test_variable_dataset)
        ret_val = self.imos.check_quality_variable_dimensions(self.test_variable_dataset)

        self.assertTrue(ret_val != None)
        self.assertTrue(len(ret_val) == 2)

        self.assertTrue(ret_val[0].value)
        self.assertFalse(ret_val[1].value)

    def test_check_quality_variable_standard_name(self):
        self.imos.setup(self.test_variable_dataset)
        
        ret_val = self.imos.check_quality_variable_standard_name(self.test_variable_dataset)

        self.assertTrue(ret_val != None)
        self.assertTrue(len(ret_val) > 0)

        self.assertTrue(ret_val[0].value)
        self.assertFalse(ret_val[1].value)

    def test_check_geospatial_lat_units(self):
        ret_val = self.imos.check_geospatial_lat_units(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_geospatial_lat_units(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_vertical_variable(self.missing_dataset)

        self.assertTrue(len(ret_val) == 0)

    def test_check_geospatial_lon_units(self):
        ret_val = self.imos.check_geospatial_lon_units(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_geospatial_lon_units(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_geospatial_lon_units(self.missing_dataset)

        self.assertTrue(len(ret_val) == 0)

    def test_check_geospatial_vertical_positive(self):
        ret_val = self.imos.check_geospatial_vertical_positive(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_geospatial_vertical_positive(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_geospatial_vertical_positive(self.missing_dataset)

        self.assertTrue(len(ret_val) == 0)

    def test_check_author_email(self):
        ret_val = self.imos.check_author_email(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_author_email(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_author_email(self.missing_dataset)

        self.assertTrue(len(ret_val) == 0)

    def test_check_principal_investigator_email(self):
        ret_val = self.imos.check_principal_investigator_email(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_principal_investigator_email(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_principal_investigator_email(self.missing_dataset)

        self.assertTrue(len(ret_val) == 0)

    def test_check_quality_control_set(self):
        ret_val = self.imos.check_quality_control_set(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_quality_control_set(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_quality_control_set(self.missing_dataset)

        self.assertTrue(len(ret_val) == 0)

    def test_check_local_time_zone(self):
        ret_val = self.imos.check_local_time_zone(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_local_time_zone(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_local_time_zone(self.missing_dataset)

        self.assertTrue(len(ret_val) == 0)

    def test_check_geospatial_vertical_units(self):
        ret_val = self.imos.check_geospatial_vertical_units(self.good_dataset)

        for result in ret_val:
            self.assertTrue(result.value)

        ret_val = self.imos.check_geospatial_vertical_units(self.bad_dataset)

        for result in ret_val:
            self.assertFalse(result.value)

        ret_val = self.imos.check_geospatial_vertical_units(self.missing_dataset)

        self.assertTrue(len(ret_val) == 0)
