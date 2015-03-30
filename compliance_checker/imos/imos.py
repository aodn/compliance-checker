#!/usr/bin/env python
'''
Compliance Test Suite for the Integrated Marine Observing System
http://www.imos.org.au/
'''

from numbers import Number
from numpy import amax
from numpy import amin
from compliance_checker.base import BaseCheck, BaseNCCheck, Result
from netCDF4 import Dataset
 
class IMOSCheck(BaseNCCheck):

    @classmethod
    def beliefs(cls):
        return {}

    def setup(self, ds):
        pass

    def check_global_attributes(self, ds):
        """
        Check to ensure all global string attributes are not empty.
        """
        ret_val = []
        result = None

        for name in ds.dataset.ncattrs():
            attribute_value = getattr(ds.dataset, name)
            if isinstance(attribute_value, basestring):
                result_name = ('globalattr', name,'check_attribute_empty')
                reasoning = None
                if not attribute_value:
                    #empty global attribute
                    reasoning = ["Attribute value is empty"]

                result = Result(BaseCheck.HIGH, reasoning == None, result_name, reasoning)
                ret_val.append(result)

        return ret_val

    def check_variable_attributes(self, ds):
        """
        Check to ensure all variable string attributes are not empty.
        """
        ret_val = []
        result = None

        for variable_name, variable in ds.dataset.variables.iteritems():
            for attribute_name in variable.ncattrs():
                attribute_value = getattr(variable, attribute_name)

                if isinstance(attribute_value, basestring):
                    result_name = ('var', variable_name, attribute_name,'check_attribute_empty')
                    reasoning = None
                    if not attribute_value:
                        #empty variable attribute
                        reasoning = ["Attribute value is empty"]

                    result = Result(BaseCheck.HIGH, reasoning == None, result_name, reasoning)
                    ret_val.append(result)

        return ret_val

    def check_project_attribute(self, ds):
        """
        Check the global project attribute and ensure it has value
        'Integrated Marine Observing System (IMOS)'
        """
        ret_val = []
        result_name = ('globalattr', 'project','check_attributes')

        result = self._check_attribute_equal("project",
                                             "Integrated Marine Observing System (IMOS)",
                                             ds,
                                             result_name,
                                             BaseCheck.HIGH)

        ret_val.append(result)
        return ret_val

    def _check_attribute_equal(self, name, value, ds, result_name, check_priority, reasoning=None, skip_check_presnet=False):
        """
        Help method to check whether an attribute equals to value. It also returns
        a Result object based on the whether the check is successful.

        params:
            name (str): attribute name
            value (str): expected value
            ds (Dataset): netcdf data file
            result_name: the result name to display
            check_priority (int): the check priority
            reasoning (str): reason string for failed check
            skip_check_presnet (boolean): flag to allow check only performed
                                         if attribute is present
        return:
            result (Result): result for the check
        """
        result = None
        global_attributes = ds.dataset.ncattrs()

        if name not in global_attributes:
            if not skip_check_presnet:
                if not reasoning:
                    reasoning = ["Attribute is not present"]

                result = Result(BaseCheck.HIGH, False, result_name, reasoning)
        else:
            attribute_value = getattr(ds.dataset, name)
            if attribute_value != value:
                if not reasoning:
                    reasoning = ["Attribute value is not equal to " + value]

                result = Result(check_priority, False, result_name, reasoning)
            else:
                result = Result(check_priority, True, result_name, None)

        return result        

    def check_naming_authority(self, ds):
        """
        Check the global naming authority attribute and ensure it has value 'IMOS'
        """
        ret_val = []
        result_name = ('globalattr', 'naming_authority','check_attributes')

        result = self._check_attribute_equal('naming_authority',
                                             "IMOS",
                                             ds,
                                             result_name,
                                             BaseCheck.HIGH)

        ret_val.append(result)

        return ret_val

    def check_data_centre(self, ds):
        """
        Check the global data centre attribute and ensure it has value
        'eMarine Information Infrastructure (eMII)'
        """
        ret_val = []
        result_name = ('globalattr', 'data_centre', 'check_attributes')
        result = self._check_attribute_equal('data_centre',
                                             "eMarine Information Infrastructure (eMII)",
                                             ds,
                                             result_name,
                                             BaseCheck.HIGH)

        ret_val.append(result)
        return ret_val

    def _check_attribute_type(self, name, type, ds, result_name, check_priority, reasoning=None, skip_check_presnet=False):
        """
        Check global data attribute and ensure it has the right type.
        params:
            name (str): attribute name
            type (class): expected type
            ds (Dataset): netcdf data file
            result_name: the result name to display
            check_priority (int): the check priority
            reasoning (str): reason string for failed check
            skip_check_presnet (boolean): flag to allow check only performed
                                         if attribute is present
        return:
            result (Result): result for the check
        """
        result = None
        global_attributes = ds.dataset.ncattrs()

        if name not in global_attributes:
            if not skip_check_presnet:
                reasoning = ["Attribute is not present"]
                result = Result(BaseCheck.HIGH, False, result_name, reasoning)
        else:
            attribute_value = getattr(ds.dataset, name)
            if not isinstance(attribute_value, type):
                if not reasoning:
                    reasoning = ["Attribute type is not equal to " + str(type)]
                result = Result(check_priority, False, result_name, reasoning)
            else:
                result = Result(check_priority, True, result_name, None)

        return result

    def check_author(self, ds):
        """
        Check the global author attribute and ensure it is str type.
        """
        ret_val = []
        result_name = ('globalattr', 'author', 'check_attribute_type')
        reasoning = ["Attribute type is not str"]
        result = self._check_attribute_type("author",
                                             basestring,
                                             ds,
                                             result_name,
                                             BaseCheck.HIGH,
                                             reasoning,
                                             False)
        if result:
            ret_val.append(result)

        return ret_val

    def check_geospatial_lat_min_max(self, ds):
        """
        Check the global geospatial_lat_min and geospatial_lat_max attributes
        match range in data and numeric type
        """

        ret_val = []
        reasoning = ["Attribute type is not numeric"]
        result_name = ('globalattr', 'geospatial_lat_min', 'check_attribute_type')
        result = self._check_attribute_type("geospatial_lat_min",
                                            Number,
                                            ds,
                                            result_name,
                                            BaseCheck.HIGH, reasoning)

        if result:
            ret_val.append(result)

        # Check to ensure attribute is present
        latitude_names = ['latitude', 'LATITUDE']
        latitude_var = None

        if result.value:
            geospatial_lat_min = getattr(ds.dataset, "geospatial_lat_min", None)

            for latitude_name in latitude_names:
                latitude_var = ds.dataset.variables.get(latitude_name, None)

                if latitude_var != None:
                    break

            if latitude_var != None:
                passed = True
                result_name = ('globalattr', 'geospatial_lat_min','check_minimum_value')
                reasoning = None
                min_value = amin(latitude_var.__array__())

                if min_value != float(geospatial_lat_min):
                    reasoning = ["Minimum value is not same as the attribute value"]
                    passed = False

                result = Result(BaseCheck.HIGH, passed, result_name, reasoning)
                ret_val.append(result)
            else:
                result_name = ('var', latitude_var.name,'check_variable_present')
                reasoning = ['Variable is not present']
                result = Result(BaseCheck.HIGH, False, result_name, reasoning)
                ret_val.append(result)

        return ret_val
