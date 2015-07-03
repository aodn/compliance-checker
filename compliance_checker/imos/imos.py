#!/usr/bin/env python
'''
Compliance Test Suite for the Integrated Marine Observing System
http://www.imos.org.au/
'''

from numbers import Number
from numpy import amax
from numpy import amin
from compliance_checker.base import BaseCheck, BaseNCCheck, Result
import datetime
import numpy as np
from util import is_monotonic
from util import is_numeric
from util import find_ancillary_variables
from util import find_data_variables
from util import find_quality_control_variables
from util import find_ancillary_variables_by_variable
from util import is_valid_email
from compliance_checker.cf.util import find_coord_vars, units_convertible, _possibleaxis, _possibleaxisunits, _possibleaxisunits
from types import IntType

class IMOSCheck(BaseNCCheck):
    register_checker = True
    name = 'imos'
    
    CHECK_VARIABLE = 1
    CHECK_GLOBAL_ATTRIBUTE = 0
    CHECK_VARIABLE_ATTRIBUTE = 3
    
    OPERATOR_EQUAL = 1
    OPERATOR_MIN = 2
    OPERATOR_MAX = 3
    OPERATOR_WITHIN = 4
    OPERATOR_DATE_FORMAT = 5
    OPERATOR_SUB_STRING = 6
    OPERATOR_CONVERTIBLE = 7
    OPERATOR_EMAIL = 8

    @classmethod
    def beliefs(cls):
        return {}

    def setup(self, ds):
        self._coordinate_variables = find_coord_vars(ds.dataset)
        self._ancillary_variables = find_ancillary_variables(ds.dataset)
        
        self._data_variables = find_data_variables(ds.dataset, self._coordinate_variables, self._ancillary_variables)
        
        self._quality_control_variables = find_quality_control_variables(ds.dataset)

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

        result = self._check_value(("project",),
                                    "Integrated Marine Observing System (IMOS)",
                                    IMOSCheck.OPERATOR_EQUAL,
                                    ds,                                    
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

        ret_val.append(result)
        return ret_val

    def _check_present(self, name, ds, check_type, result_name, check_priority, reasoning=None):
        """
        Help method to check whether a variable, variable attribute
        or a global attribute presents.

        params:
            name (tuple): variable name and attribute name.
                          For global attribute, only attribute name present.
            ds (Dataset): netcdf data file
            check_type (int): CHECK_VARIABLE, CHECK_GLOBAL_ATTRIBUTE,
                              CHECK_VARIABLE_ATTRIBUTE
            result_name: the result name to display
            check_priority (int): the check priority
            reasoning (str): reason string for failed check
        return:
            result (Result): result for the check
        """

        passed = True

        if check_type == IMOSCheck.CHECK_GLOBAL_ATTRIBUTE:
            if not result_name:
                result_name = ('globalattr', name[0],'check_attribute_present')
            if name[0] not in ds.dataset.ncattrs():
                if not reasoning:
                    reasoning = ["Attribute is not present"]
                    passed = False

        if check_type == IMOSCheck.CHECK_VARIABLE or\
            check_type == IMOSCheck.CHECK_VARIABLE_ATTRIBUTE:
            if not result_name:
                result_name = ('var', name[0],'check_variable_present')

            variable = ds.dataset.variables.get(name[0], None)

            if variable == None:
                if not reasoning:
                    reasoning = ['Variable is not present']
                passed = False

            else:
                if check_type == IMOSCheck.CHECK_VARIABLE_ATTRIBUTE:
                    if not result_name:
                        result_name = ('var', name[0], name[1], 'check_variable_attribute_present')
                    if name[1] not in variable.ncattrs():
                        if not reasoning:
                            reasoning = ["Variable attribute is not present"]
                        passed = False

        result = Result(check_priority, passed, result_name, reasoning)

        return result

    def _check_value(self, name, value, operator, ds, check_type, result_name, check_priority, reasoning=None, skip_check_presnet=False):
        """
        Help method to compare attribute to value or a variable
        to a value. It also returns a Result object based on the whether
        the check is successful.

        params:
            name (tuple): variable name and attribute name.
                          For global attribute, only attribute name present.
            value (str): expected value
            operator (int): OPERATOR_EQUAL, OPERATOR_MAX, OPERATOR_MIN
            ds (Dataset): netcdf data file
            check_type (int): CHECK_VARIABLE, CHECK_GLOBAL_ATTRIBUTE,
                              CHECK_VARIABLE_ATTRIBUTE
            result_name: the result name to display
            check_priority (int): the check priority
            reasoning (str): reason string for failed check
            skip_check_presnet (boolean): flag to allow check only performed
                                         if attribute is present
        return:
            result (Result): result for the check
        """
        result = self._check_present(name, ds, check_type,
                            result_name,
                            BaseCheck.HIGH)

        if result.value:
            result = None
            retrieved_value = None
            passed = True

            if check_type == IMOSCheck.CHECK_GLOBAL_ATTRIBUTE:
                retrieved_value = getattr(ds.dataset, name[0])

            if check_type == IMOSCheck.CHECK_VARIABLE:
                variable = ds.dataset.variables.get(name[0], None)

            if check_type == IMOSCheck.CHECK_VARIABLE_ATTRIBUTE:
                variable = ds.dataset.variables.get(name[0], None)
                retrieved_value = getattr(variable, name[1])

            if operator == IMOSCheck.OPERATOR_EQUAL:
                if retrieved_value != value:
                    if not reasoning:
                        reasoning = ["Attribute value is not equal to " + str(value)]
                        passed = False

            if operator == IMOSCheck.OPERATOR_MIN:
                min_value = amin(variable.__array__())

                if min_value != float(value):
                    passed = False
                    if not reasoning:
                        reasoning = ["Minimum value is not same as the attribute value"]

            if operator == IMOSCheck.OPERATOR_MAX:
                max_value = amax(variable.__array__())
                if max_value != float(value):
                    passed = False
                    if not reasoning:
                        reasoning = ["Maximum value is not same as the attribute value"]

            if operator == IMOSCheck.OPERATOR_DATE_FORMAT:
                try:
                    datetime.datetime.strptime(retrieved_value, value)
                except ValueError:
                    passed = False
                    if not reasoning:
                        reasoning = ["Datetime format is not correct"]

            if operator == IMOSCheck.OPERATOR_SUB_STRING:
                if value not in retrieved_value:
                    passed = False
                    if not reasoning:
                        reasoning = ["Required substring is not contained"]

            if operator == IMOSCheck.OPERATOR_CONVERTIBLE:
                if not units_convertible(retrieved_value, value):
                    passed = False
                    if not reasoning:
                        reasoning = ["Value is not convertible"]

            if operator == IMOSCheck.OPERATOR_EMAIL:
                if not is_valid_email(retrieved_value):
                    passed = False
                    if not reasoning:
                        reasoning = ["Value is not a valid email"]

            if operator == IMOSCheck.OPERATOR_WITHIN:
                if retrieved_value not in value:
                    passed = False
                    if not reasoning:
                        reasoning = ["Value is not in the expected range"]

            result = Result(BaseCheck.HIGH, passed, result_name, reasoning)

        else:
            if skip_check_presnet:
                result = None

        return result

    def check_naming_authority(self, ds):
        """
        Check the global naming authority attribute and ensure it has value 'IMOS'
        """
        ret_val = []
        result_name = ('globalattr', 'naming_authority','check_attributes')

        result = self._check_value(('naming_authority',),
                                    "IMOS",
                                    IMOSCheck.OPERATOR_EQUAL,
                                    ds,
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
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
        result = self._check_value(('data_centre',),
                                    "eMarine Information Infrastructure (eMII)",
                                    IMOSCheck.OPERATOR_EQUAL,
                                    ds,                                
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

        ret_val.append(result)
        return ret_val

    def _check_attribute_type(self, name, type, ds, check_type, result_name, check_priority, reasoning=None, skip_check_presnet=False):
        """
        Check global data attribute and ensure it has the right type.
        params:
            name (tuple): attribute name
            type (class): expected type
            ds (Dataset): netcdf data file
            check_type (int): CHECK_VARIABLE, CHECK_GLOBAL_ATTRIBUTE,
                              CHECK_VARIABLE_ATTRIBUTE
            result_name: the result name to display
            check_priority (int): the check priority
            reasoning (str): reason string for failed check
            skip_check_presnet (boolean): flag to allow check only performed
                                         if attribute is present
        return:
            result (Result): result for the check
        """
        result = self._check_present(name, ds, check_type,
                            result_name,
                            BaseCheck.HIGH)

        if result.value:
            if check_type == IMOSCheck.CHECK_GLOBAL_ATTRIBUTE:
                attribute_value = getattr(ds.dataset, name[0])

            if check_type == IMOSCheck.CHECK_VARIABLE_ATTRIBUTE:
                attribute_value = getattr(ds.dataset.variables[name[0]], name[1])

            if check_type == IMOSCheck.CHECK_VARIABLE:
                attribute_value = ds.dataset.variables[name[0]]

            dtype = getattr(attribute_value, 'dtype', None)
            passed = True

            if not dtype is None:
                if dtype != type:
                    passed = False
            else:
                try:
                    if not isinstance(attribute_value, type):
                        passed = False
                except TypeError:
                    passed = False

            if not passed:
                if not reasoning:
                    reasoning = ["Attribute type is not equal to " + str(type)]
                result = Result(check_priority, False, result_name, reasoning)
            else:
                result = Result(check_priority, True, result_name, None)
        else:
            if skip_check_presnet:
                result = None

        return result

    def check_author(self, ds):
        """
        Check the global author attribute and ensure it is str type.
        """
        return self._check_str_type(ds, "author")

    def check_geospatial_lat_min_max(self, ds):
        """
        Check the global geospatial_lat_min and geospatial_lat_max attributes
        match range in data and numeric type
        """
        ret_val = []

        result_name = ('globalattr', 'geospatial_lat_min', 'check_attribute_type')
        result = self._check_present(('LATITUDE',), ds, IMOSCheck.CHECK_VARIABLE,
                                     result_name,
                                     BaseCheck.HIGH)

        if result.value:
            result_name = ('globalattr', 'geospatial_lat_min', 'check_attribute_type')
            result = self._check_attribute_type(('geospatial_lat_min',),
                                            np.number,
                                            ds,
                                            IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                            result_name,
                                            BaseCheck.HIGH,
                                            ["Attribute type is not numeric"])

            if result:
                ret_val.append(result)

            if result.value:
                geospatial_lat_min = getattr(ds.dataset, "geospatial_lat_min", None)
                result_name = ('globalattr', 'geospatial_lat_min','check_minimum_value')
                result = self._check_value(('LATITUDE',),
                                           geospatial_lat_min,
                                           IMOSCheck.OPERATOR_MIN,
                                           ds,
                                           IMOSCheck.CHECK_VARIABLE,
                                           result_name,
                                           BaseCheck.HIGH)
                ret_val.append(result)

            result_name = ('globalattr', 'geospatial_lat_max', 'check_attribute_type')
            result2 = self._check_attribute_type(('geospatial_lat_max',),
                                                np.number,
                                                ds,
                                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                                result_name,
                                                BaseCheck.HIGH,
                                                ["Attribute type is not numeric"])
            if result2:
                ret_val.append(result2)

            if result2.value:
                geospatial_lat_max = getattr(ds.dataset, "geospatial_lat_max", None)
                result_name = ('globalattr', 'geospatial_lat_max','check_maximum_value')
                result = self._check_value(('LATITUDE',),
                                           geospatial_lat_max,
                                           IMOSCheck.OPERATOR_MAX,
                                           ds,
                                           IMOSCheck.CHECK_VARIABLE,
                                           result_name,
                                           BaseCheck.HIGH)
                ret_val.append(result)

        return ret_val

    def check_geospatial_lon_min_max(self, ds):
        """
        Check the global geospatial_lon_min and geospatial_lon_max attributes
        match range in data and numeric type
        """
        ret_val = []

        result_name = ('globalattr', 'geospatial_lon_min', 'check_attribute_type')
        result = self._check_present(('LONGITUDE',), ds, IMOSCheck.CHECK_VARIABLE,
                                     result_name,
                                     BaseCheck.HIGH)

        if result.value:
            result_name = ('globalattr', 'geospatial_lon_min', 'check_attribute_type')
            result = self._check_attribute_type(('geospatial_lon_min',),
                                                np.number,
                                                ds,
                                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                                result_name,
                                                BaseCheck.HIGH,
                                                ["Attribute type is not numeric"])

            if result:
                ret_val.append(result)

            if result.value:
                geospatial_lon_min = getattr(ds.dataset, "geospatial_lon_min", None)
                result_name = ('globalattr', 'geospatial_lon_min','check_minimum_value')
                result = self._check_value(('LONGITUDE',),
                                           geospatial_lon_min,
                                           IMOSCheck.OPERATOR_MIN,
                                           ds,
                                           IMOSCheck.CHECK_VARIABLE,
                                           result_name,
                                           BaseCheck.HIGH)
                ret_val.append(result)

            result_name = ('globalattr', 'geospatial_lon_max', 'check_attribute_type')
            result2 = self._check_attribute_type(('geospatial_lon_max',),
                                                np.number,
                                                ds,
                                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                                result_name,
                                                BaseCheck.HIGH,
                                                ["Attribute type is not numeric"])
            if result2:
                ret_val.append(result2)

            if result2.value:
                geospatial_lon_max = getattr(ds.dataset, "geospatial_lon_max", None)
                result_name = ('globalattr', 'geospatial_lon_max','check_maximum_value')
                result = self._check_value(('LONGITUDE',),
                                           geospatial_lon_max,
                                           IMOSCheck.OPERATOR_MAX,
                                           ds,
                                           IMOSCheck.CHECK_VARIABLE,
                                           result_name,
                                           BaseCheck.HIGH)
                ret_val.append(result)

        return ret_val

    def check_geospatial_vertical_min_max(self, ds):
        """
        Check the global geospatial_vertical_min and 
        geospatial_vertical_max attributes match range in data and numeric type
        """
        ret_val = []

        result_name = ('globalattr', 'geospatial_vertical_min', 'check_attribute_type')
        result = self._check_present(('VERTICAL',), ds, IMOSCheck.CHECK_VARIABLE,
                                     result_name,
                                     BaseCheck.HIGH)

        if result.value:
            result_name = ('globalattr', 'geospatial_vertical_min', 'check_attribute_type')
            result = self._check_attribute_type(('geospatial_vertical_min',),
                                                np.number,
                                                ds,
                                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                                result_name,
                                                BaseCheck.HIGH,
                                                ["Attribute type is not numeric"])

            if result:
                ret_val.append(result)

            if result.value:
                geospatial_lat_min = getattr(ds.dataset, "geospatial_vertical_min", None)
                result_name = ('globalattr', 'geospatial_vertical_min','check_minimum_value')
                result = self._check_value(('VERTICAL',),
                                           geospatial_lat_min,
                                           IMOSCheck.OPERATOR_MIN,
                                           ds,
                                           IMOSCheck.CHECK_VARIABLE,
                                           result_name,
                                           BaseCheck.HIGH)
                ret_val.append(result)

            result_name = ('globalattr', 'geospatial_vertical_max', 'check_attribute_type')
            result2 = self._check_attribute_type(('geospatial_vertical_max',),
                                                np.number,
                                                ds,
                                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                                result_name,
                                                BaseCheck.HIGH,
                                                ["Attribute type is not numeric"])
            if result2:
                ret_val.append(result2)

            if result2.value:
                geospatial_lat_max = getattr(ds.dataset, "geospatial_vertical_max", None)
                result_name = ('globalattr', 'geospatial_vertical_max','check_maximum_value')
                result = self._check_value(('VERTICAL',),
                                           geospatial_lat_max,
                                           IMOSCheck.OPERATOR_MAX,
                                           ds,
                                           IMOSCheck.CHECK_VARIABLE,
                                           result_name,
                                           BaseCheck.HIGH)
                ret_val.append(result)

        return ret_val

    def check_time_coverage(self, ds):
        """
        Check the global attributes time_coverage_start/time_coverage_end whether
        match format 'YYYY-MM-DDThh:mm:ssZ'
        """
        ret_val = []
        result_name = ('globalattr', 'time_coverage_start','check_date_format')

        result = self._check_present(('TIME',), ds, IMOSCheck.CHECK_VARIABLE,
                                     result_name,
                                     BaseCheck.HIGH)

        if result.value:
            results = self._check_str_type(ds, 'time_coverage_start')
            result = results[0]
            if result.value:
                result_name = ('globalattr', 'time_coverage_start','check_date_format')
                result = self._check_value(('time_coverage_start',),
                                        '%Y-%m-%dT%H:%M:%SZ',
                                        IMOSCheck.OPERATOR_DATE_FORMAT,
                                        ds,
                                        IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)
            ret_val.append(result)

            results = self._check_str_type(ds, 'time_coverage_end')
            result = results[0]
            if result.value:
                result_name = ('globalattr', 'time_coverage_end','check_date_format')
                result = self._check_value(('time_coverage_end',),
                                        '%Y-%m-%dT%H:%M:%SZ',
                                        IMOSCheck.OPERATOR_DATE_FORMAT,
                                        ds,
                                        IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)
            ret_val.append(result)

        return ret_val

    def check_title(self, ds):
        """
        Check the global attributes title has string type
        """
        return self._check_str_type(ds, "title")

    def check_date_created(self, ds):
        """
        Check the global attributes date_created whether
        match format 'YYYY-MM-DDThh:mm:ssZ'
        """
        ret_val = []

        result_name = ('globalattr', 'date_created','check_date_format')
        result = self._check_value(('date_created',),
                                    '%Y-%m-%dT%H:%M:%SZ',
                                    IMOSCheck.OPERATOR_DATE_FORMAT,
                                    ds,
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)
        ret_val.append(result)

        return ret_val


    def _check_str_type(self, ds, name):
        """
        Check the global attribute has string type

        params:
            name (str): attribute name
        return:
            result (list): a list of Result objects
        """
        ret_val = []

        result_name = ('globalattr', name, 'check_atttribute_type')
        reasoning = ["Attribute type is not string"]

        result = self._check_attribute_type((name,),
                                             basestring,
                                             ds,
                                             IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                             result_name,
                                             BaseCheck.HIGH,
                                             reasoning,
                                             False)

        ret_val.append(result)

        return ret_val

    def check_abstract(self, ds):
        """
        Check the global attributes abstract has string type
        """
        return self._check_str_type(ds, "abstract")
    
    
    def _check_global_value_equal(self, ds, name, value):
        """
        Check global attribute to has the required value.
        
        params:
            name (str): attribute name
        return:
            result (list): a list of Result objects
            
        """
        ret_val = []
        result_name = ('globalattr', name,'check_attributes')

        result = self._check_value((name,),
                                    value,
                                    IMOSCheck.OPERATOR_EQUAL,
                                    ds,
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

        ret_val.append(result)

        return ret_val

    def check_data_centre_email(self, ds):
        """
        Check the global data_centre_email and ensure it has value 'info@emii.org.au'
        """
        return self._check_global_value_equal(ds,'data_centre_email', 'info@emii.org.au')

    def check_principal_investigator(self, ds):
        return self._check_str_type(ds, 'principal_investigator')

    def check_citation(self, ds):
        return self._check_str_type(ds, 'citation')

    def check_acknowledgement(self, ds):
        """
        Check the global acknowledgement attribute and ensure it has expected
        value
        """
        ret_val = []

        result_name = ('globalattr', 'acknowledgement','check_attributes')
        value = "Data was sourced from the Integrated Marine Observing System (IMOS) - IMOS is supported by the Australian Government through the National Collaborative Research Infrastructure Strategy (NCRIS) and the Super Science Initiative (SSI)"
        ret_val = []
        result = self._check_value(('acknowledgement',),
                                    value,
                                    IMOSCheck.OPERATOR_SUB_STRING,
                                    ds,
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)
        ret_val.append(result)

        return ret_val

    def check_distribution_statement(self, ds):
        """
        Check the global distribution statement attribute and ensure it has
        expected value
        """
        ret_val = []

        result_name = ('globalattr', 'distribution_statement','check_attributes')
        value = 'Data may be re-used, provided that related metadata explaining the data has been reviewed by the user, and the data is appropriately acknowledged. Data, products and services from IMOS are provided "as is" without any warranty as to fitness for a particular purpose.'
        ret_val = []
        result = self._check_value(('distribution_statement',),
                                    value,
                                    IMOSCheck.OPERATOR_SUB_STRING,
                                    ds,
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)
        ret_val.append(result)

        return ret_val

    def check_variables_long_name(self, ds):
        """
        Check the every variable long name attribute and ensure it is string type.
        """
        ret_val = []
        for name, var in ds.dataset.variables.iteritems():
            result_name = ('var', name, 'long_name', 'check_atttribute_type')
            reasoning = ["Attribute type is not string"]

            result = self._check_attribute_type((name,'long_name',),
                                                 basestring,
                                                 ds,
                                                 IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                                 result_name,
                                                 BaseCheck.HIGH,
                                                 reasoning)
            ret_val.append(result)

        return ret_val

    def check_coordinate_variables(self, ds):
        """
        Check all coordinate variables to ensure it has numeric type (byte,
        float and integer) and also check whether it is monotonic
        """        

        space_time_checked = False

        ret_val = []
        for var in self._coordinate_variables:
            result_name = ('var', var.name, 'check_variable_type')
            passed = True
            reasoning = None
            if not is_numeric(var.datatype):
                reasoning = ["Variable type is not numeric"]
                passed = False

            result = Result(BaseCheck.HIGH, passed, result_name, reasoning)
            ret_val.append(result)

            result_name = ('var', var.name, 'check_monotonic')
            passed = True
            reasoning = None

            if not is_monotonic(var.__array__()):
                reasoning = ["Variable values are not monotonic"]

            result = Result(BaseCheck.HIGH, passed, result_name, reasoning)
            ret_val.append(result)

            result_name = ('var', 'space_time_coordinate', 'check_variable_present')
            passed = False
            reasoning = None
            if not space_time_checked:
                if str(var.name) in _possibleaxis \
                    or (hasattr(var, 'units') and (var.units in _possibleaxisunits or var.units.split(" ")[0]  in _possibleaxisunits)) \
                    or hasattr(var,'positive'):
                    space_time_checked = True
                    passed = True
                else:
                    passed = False
                    reasoning = ["No space-time coordinate variable found"]

            result = Result(BaseCheck.HIGH, passed, result_name, reasoning)
            ret_val.append(result)

        return ret_val

    def check_time_variable(self, ds):
        """
        Check time variable attributes:
            standard_name
            axis
            valid_min
            valid_max
            type
            units
        """
        ret_val = []

        result_name = ('var', 'TIME', 'check_present')
        result = self._check_present(('TIME',),
                                     ds,
                                     IMOSCheck.CHECK_VARIABLE,
                                     result_name,
                                     BaseCheck.HIGH)
        if result.value:

            result_name = ('var', 'TIME', 'standard_name', 'check_attributes')

            result = self._check_value(('TIME','standard_name',),
                                        'time',
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'TIME', 'axis', 'check_attributes')

            result = self._check_value(('TIME','axis',),
                                        'T',
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'TIME', 'valid_min', 'check_present')

            result = self._check_present(('TIME', 'valid_min'),
                                         ds,
                                         IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                         result_name,
                                         BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'TIME', 'valid_max', 'check_present')

            result = self._check_present(('TIME', 'valid_max'),
                                         ds,
                                         IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                         result_name,
                                         BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'TIME', 'calendar', 'check_attribute_value')

            result = self._check_value(('TIME','calendar',),
                                        'gregorian',
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'TIME','check_variable_type')
            reasoning = ["The Type of variable TIME is not Double"]

            result = self._check_attribute_type(('TIME',),
                                            np.float64,
                                            ds,
                                            IMOSCheck.CHECK_VARIABLE,
                                            result_name,
                                            BaseCheck.HIGH,
                                            reasoning)

            ret_val.append(result)

            result_name = ('var', 'TIME', 'units', 'check_attribute_value')
            result = self._check_value(('TIME','units',),
                                        'days since 1950-01-01 00:00:00 UTC',
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            ret_val.append(result)

        return ret_val

    def check_longitude_variable(self, ds):
        """
        Check longitude variable attributes:
            standard_name  value is 'longitude'
            axis   value is 'X'
            valid_min 0 or -180
            valid_max 360 or 180
            reference_datum is a string type
        """
        ret_val = []
        
        result_name = ('var', 'LONGITUDE', 'check_present')
        result = self._check_present(('LONGITUDE',),
                                     ds,
                                     IMOSCheck.CHECK_VARIABLE,
                                     result_name,
                                     BaseCheck.HIGH)
        
        if result.value:
            result_name = ('var', 'LONGITUDE', 'standard_name', 'check_attributes')

            result = self._check_value(('LONGITUDE','standard_name',),
                                        'longitude',
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'LONGITUDE', 'axis', 'check_attributes')

            result = self._check_value(('LONGITUDE','axis',),
                                        'X',
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'LONGITUDE', 'reference_datum', 'check_attributes')
            result = self._check_attribute_type(('LONGITUDE','reference_datum',),
                                        basestring,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            ret_val.append(result)

            result1 = self._check_value(('LONGITUDE','valid_min',),
                                        0,
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            result2 = self._check_value(('LONGITUDE','valid_max',),
                                        360,
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            result3 = self._check_value(('LONGITUDE','valid_min',),
                                        -180,
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            result4 = self._check_value(('LONGITUDE','valid_max',),
                                        180,
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            if (result1.value and result2.value) or (result3.value and result4.value):
                result_name = ('var', 'LONGITUDE', 'valid_min', 'check_min_value')
                result = Result(BaseCheck.HIGH, True, result_name, None)
                ret_val.append(result)

                result_name = ('var', 'LONGITUDE', 'valid_max', 'check_max_value')
                result = Result(BaseCheck.HIGH, True, result_name, None)
                ret_val.append(result)

            else:
                result_name = ('var', 'LONGITUDE', 'valid_min', 'check_min_value')
                reasoning = ["doesn't match value pair (0, 360) or (-180, 180)"]
                result = Result(BaseCheck.HIGH, False, result_name, reasoning)
                ret_val.append(result)

                result_name = ('var', 'LONGITUDE', 'valid_max', 'check_max_value')
                reasoning = ["doesn't match value pair (0, 360) or (-180, 180)"]
                result = Result(BaseCheck.HIGH, False, result_name, reasoning)
                ret_val.append(result)

            result_name = ('var', 'LONGITUDE', 'units', 'check_attribute_value')
            result = self._check_value(('LONGITUDE','units',),
                                        'degrees_east',
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'LONGITUDE','check_variable_type')
            reasoning = ["The Type of variable LONGITUDE is not Double or Float"]

            result1 = self._check_attribute_type(('LONGITUDE',),
                                            np.float64,
                                            ds,
                                            IMOSCheck.CHECK_VARIABLE,
                                            result_name,
                                            BaseCheck.HIGH,
                                            reasoning)

            result2 = self._check_attribute_type(('LONGITUDE',),
                                            np.float32,
                                            ds,
                                            IMOSCheck.CHECK_VARIABLE,
                                            result_name,
                                            BaseCheck.HIGH,
                                            reasoning)

            if result1.value or result2.value:
                ret_val.append(result1)
            else:
                if not result1.value:
                    ret_val.append(result1)
                if not result2.value:
                    ret_val.append(result2)

        return ret_val

    def check_latitude_variable(self, ds):
        """
        Check latitude variable attributes:
            standard_name  value is 'latitude'
            axis   value is 'Y'
            valid_min -90
            valid_max 90
            reference_datum is a string type
        """
        ret_val = []
        result_name = ('var', 'LATITUDE', 'standard_name', 'check_attributes')


        result = self._check_present(('LATITUDE',),
                                    ds,
                                    IMOSCheck.CHECK_VARIABLE,
                                    result_name,
                                    BaseCheck.HIGH)

        if result.value:
            result = self._check_value(('LATITUDE','standard_name',),
                                        'latitude',
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'LATITUDE', 'axis', 'check_attributes')

            result = self._check_value(('LATITUDE','axis',),
                                        'Y',
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'LATITUDE', 'reference_datum', 'check_attributes')
            result = self._check_attribute_type(('LATITUDE','reference_datum',),
                                        basestring,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'LATITUDE', 'valid_min', 'check_min_value')
            result = self._check_value(('LATITUDE','valid_min',),
                                        -90,
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)
            ret_val.append(result)

            result_name = ('var', 'LATITUDE', 'valid_max', 'check_max_value')
            result = self._check_value(('LATITUDE','valid_max',),
                                        90,
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)
            ret_val.append(result)

            result_name = ('var', 'LATITUDE', 'units', 'check_attribute_value')
            result = self._check_value(('LATITUDE','units',),
                                        'degrees_north',
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'LATITUDE','check_variable_type')
            reasoning = ["The Type of variable LATITUDE is not Double or Float"]

            result1 = self._check_attribute_type(('LATITUDE',),
                                            np.float64,
                                            ds,
                                            IMOSCheck.CHECK_VARIABLE,
                                            result_name,
                                            BaseCheck.HIGH,
                                            reasoning)

            result2 = self._check_attribute_type(('LATITUDE',),
                                            np.float32,
                                            ds,
                                            IMOSCheck.CHECK_VARIABLE,
                                            result_name,
                                            BaseCheck.HIGH,
                                            reasoning)

            if result1.value or result2.value:
                ret_val.append(result1)
            else:
                if not result1.value:
                    ret_val.append(result1)
                if not result2.value:
                    ret_val.append(result2)
        return ret_val

    def check_vertical_variable(self, ds):
        """
        Check vertical variable attributes:
            standard_name  value is 'depth' or 'height'
            axis   value is 'Z'
            positive value is 'down' or "up"
            valid_min exist
            valid_max exists
            reference_datum is a string type
            unit
        """
        ret_val = []

        result_name = ('var', 'VERTICAL', 'check_present')
        result = self._check_present(('VERTICAL',),
                                     ds,
                                     IMOSCheck.CHECK_VARIABLE,
                                     result_name,
                                     BaseCheck.HIGH)
        if result.value:

            result_name = ('var', 'VERTICAL', 'reference_datum', 'check_attributes')
            result = self._check_attribute_type(('VERTICAL','reference_datum',),
                                       basestring,
                                       ds,
                                       IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                       result_name,
                                       BaseCheck.HIGH)

            ret_val.append(result)

            result1 = self._check_value(('VERTICAL','standard_name',),
                              'depth',
                              IMOSCheck.OPERATOR_EQUAL, ds,
                              IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                              result_name,
                              BaseCheck.HIGH)

            result2 = self._check_value(('VERTICAL','standard_name',),
                              'height',
                              IMOSCheck.OPERATOR_EQUAL, ds,
                              IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                              result_name,
                              BaseCheck.HIGH)

            result3 = self._check_value(('VERTICAL','positive',),
                              'down',
                              IMOSCheck.OPERATOR_EQUAL, ds,
                              IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                              result_name,
                              BaseCheck.HIGH)

            result4 = self._check_value(('VERTICAL','positive',),
                              'up',
                              IMOSCheck.OPERATOR_EQUAL, ds,
                              IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                              result_name,
                              BaseCheck.HIGH)


            if (result1.value and result3.value) or (result2.value and result4.value):
                result_name = ('var', 'VERTICAL', 'positive', 'check_value')
                result = Result(BaseCheck.HIGH, True, result_name, None)
                ret_val.append(result)
                result_name = ('var', 'VERTICAL', 'standard_name', 'check_value')
                result = Result(BaseCheck.HIGH, True, result_name, None)
                ret_val.append(result)
            else:
                result_name = ('var', 'VERTICAL', 'positive', 'check_value')
                reasoning = ["doesn't have value pair (depth, down) or (height, up)"]
                result = Result(BaseCheck.HIGH, False, result_name, reasoning)
                ret_val.append(result)
                result_name = ('var', 'VERTICAL', 'standard_name', 'check_value')
                reasoning = ["doesn't have value pair (depth, down) or (height, up)"]
                result = Result(BaseCheck.HIGH, False, result_name, reasoning)
                ret_val.append(result)

            result_name = ('var', 'VERTICAL', 'valid_min', 'check_present')

            result = self._check_present(('VERTICAL', 'valid_min'),
                                         ds,
                                         IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                         result_name,
                                         BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'VERTICAL', 'valid_max', 'check_present')

            result = self._check_present(('VERTICAL', 'valid_max'),
                                         ds,
                                         IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                         result_name,
                                         BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'VERTICAL', 'axis', 'check_attributes')

            result = self._check_value(('VERTICAL','axis',),
                                        'Z',
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'VERTICAL', 'units', 'check_attributes')
            reasoning = ["units is not a valid CF distance unit"]
            result = self._check_value(('VERTICAL','units',),
                                        'meter',
                                        IMOSCheck.OPERATOR_CONVERTIBLE,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH,
                                        reasoning)

            ret_val.append(result)

            result_name = ('var', 'VERTICAL','check_variable_type')
            reasoning = ["The Type of variable VERTICAL is not Double or Float"]

            result1 = self._check_attribute_type(('VERTICAL',),
                                            np.float64,
                                            ds,
                                            IMOSCheck.CHECK_VARIABLE,
                                            result_name,
                                            BaseCheck.HIGH,
                                            reasoning)

            result2 = self._check_attribute_type(('VERTICAL',),
                                            np.float32,
                                            ds,
                                            IMOSCheck.CHECK_VARIABLE,
                                            result_name,
                                            BaseCheck.HIGH,
                                            reasoning)

            if result1.value or result2.value:
                ret_val.append(result1)
            else:
                if not result1.value:
                    ret_val.append(result1)
                if not result2.value:
                    ret_val.append(result2)

        return ret_val

    def check_variable_attribute_type(self, ds):
        """
        Check variable attribute to ensure it has the same type as the variable
        """

        ret_val = []
        reasoning = ["Attribute type is not same as variable type"]
        for name,var in ds.dataset.variables.iteritems():
            result_name = ('var', name, '_FillValue', 'check_attribute_type')
            result = self._check_attribute_type((name,'_FillValue',),
                                                var.datatype,
                                                ds,
                                                IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                                result_name,
                                                BaseCheck.HIGH,
                                                reasoning,
                                                True)
            if not result is None:
                ret_val.append(result)

            result_name = ('var', name, 'valid_min', 'check_attribute_type')
          
            result = self._check_attribute_type((name,'valid_min',),
                                                var.datatype,
                                                ds,
                                                IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                                result_name,
                                                BaseCheck.HIGH,
                                                reasoning,
                                                True)
            if not result is None:
                ret_val.append(result)

            result_name = ('var', name, 'valid_max', 'check_attribute_type')            
            result = self._check_attribute_type((name,'valid_max',),
                                                var.datatype,
                                                ds,
                                                IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                                result_name,
                                                BaseCheck.HIGH,
                                                reasoning,
                                                True)
            if not result is None:
                ret_val.append(result)

        return ret_val

    def check_data_variables(self, ds):
        """
        Check data variable:
            at least one data variable exisits
        """
        ret_val = []
        result_name = ('var', 'data_variable', 'check_data_variable_present')
        if len(self._data_variables) == 0:
            result = Result(BaseCheck.HIGH, False, result_name, ["No data variable exists"])
        else:
            result = Result(BaseCheck.HIGH, True, result_name, None)

        ret_val.append(result)

        if result.value:
            required_dimensions = ['TIME', 'LATITUDE', 'LONGITUDE', 'DEPTH']

            for var in self._data_variables:
                result_name = ('var', 'data_variable', var.name, 'check_dimension')
                passed = True
                reasoning = None

                if len(var.dimensions) > 0:
                    for dimension in var.dimensions:
                        if dimension in required_dimensions:
                            passed = True
                        else:
                            passed = False
                else:
                    passed = False

                if not passed:
                    reasoning =  ["dimension doesn't contain TIME, LATITUDE, LONGITUDE, DEPTH"]

                result = Result(BaseCheck.HIGH, passed, result_name, reasoning)

                ret_val.append(result)
                
                result_name = ('var', 'data_variable', var.name, 'units', 'check_attribute_type')
                result = None
                result = self._check_attribute_type((var.name,"units",),
                                           basestring,
                                           ds,
                                           IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                           result_name,
                                           BaseCheck.HIGH,
                                           None,
                                           True)
                if result is not None:
                    ret_val.append(result)

                result_name = ('var', 'data_variable', var.name, '_FillValue', 'check_attribute_type')
                reasoning = ["Attribute type is not same as variable type"]
                result = None
                result = self._check_attribute_type((var.name,'_FillValue',),
                                                var.datatype,
                                                ds,
                                                IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                                result_name,
                                                BaseCheck.HIGH,
                                                reasoning,
                                                True)
                if result is not None:
                    ret_val.append(result)

                result_name = ('var', 'data_variable', var.name, 'valid_min', 'check_attribute_type')
                reasoning = ["Attribute type is not same as variable type"]
                result = None
                result = self._check_attribute_type((var.name,'valid_min',),
                                                var.datatype,
                                                ds,
                                                IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                                result_name,
                                                BaseCheck.HIGH,
                                                reasoning,
                                                True)
                if result is not None:
                    ret_val.append(result)

                result_name = ('var', 'data_variable', var.name, 'valid_max', 'check_attribute_type')
                reasoning = ["Attribute type is not same as variable type"]
                result = None
                result = self._check_attribute_type((var.name,'valid_max',),
                                                var.datatype,
                                                ds,
                                                IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                                result_name,
                                                BaseCheck.HIGH,
                                                reasoning,
                                                True)
                if result is not None:
                    ret_val.append(result)

        return ret_val

    def check_quality_control_set_for_quality_control_variable(self, ds):
        """
        Check value of quality_control_set attribute is one of (1,2,3,4),
        for quality control variables
        """
        ret_val = []

        for qc_variable in self._quality_control_variables:
            result_name = ('var', 'quality_variable', qc_variable.name, 'check_attributes')    
            result = self._check_value((qc_variable.name,'quality_control_set',),
                                    [1,2,3,4],
                                    IMOSCheck.OPERATOR_WITHIN,
                                    ds,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.MEDIUM)

            if result is not None:
                ret_val.append(result)

        return ret_val
    
    def check_quality_control_conventions_for_quality_control_variable(self, ds):
        """
        Check value of quality_control_conventions attribute matchs
        the quality_control_set attribute
        """
        
        test_value_dict = {'1': "IMOS standard set using the IODE flags",\
                           '2': "ARGO quality control procedure",\
                           '3': "BOM (SST and Air-Sea flux) quality control procedure",\
                           '4': "WOCE quality control procedure (Multidisciplinary Underway Network - CO 2 measurements)"}               
        
        ret_val = []

        for qc_variable in self._quality_control_variables:
            key = str(int(qc_variable.quality_control_set))
            
            if key in test_value_dict:
                test_value = test_value_dict[key]

                result_name = ('var', 'quality_variable', qc_variable.name, 'check_attributes')
                reasoning = ["quality_control_conventions doesn't match value in quality_control_set"]

                result = self._check_value((qc_variable.name,'quality_control_conventions',),
                                        test_value,
                                        IMOSCheck.OPERATOR_EQUAL,
                                        ds,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.MEDIUM,
                                        reasoning)

                if result is not None:
                    ret_val.append(result)

        return ret_val

    def check_quality_control_variable_dimensions(self, ds):
        """
        Check quality variable has same dimensions as the related data variable.
        """
        ret_val = []
        for qc_variable in self._quality_control_variables:
            for data_variable in self._data_variables:
                ancillary_variables = find_ancillary_variables_by_variable(ds.dataset, data_variable)
                if qc_variable in ancillary_variables:
                    result_name = ('var', 'quality_variable', qc_variable.name, data_variable.name, 'check_dimension')
                    if data_variable.dimensions == qc_variable.dimensions:
                        result = Result(BaseCheck.HIGH, True, result_name, None)
                    else:
                        reasoning = ["Dimension is not same"]
                        result = Result(BaseCheck.HIGH, False, result_name, reasoning)
                    
                    ret_val.append(result)

        return ret_val

    def check_quality_control_variable_listed(self, ds):
        """
        Check quality control variable is listed in the related data variable's
        ancillary_variables attribute.
        """
        ret_val = []

        for data_variable in self._data_variables:
            ancillary_variables = find_ancillary_variables_by_variable(ds.dataset, data_variable)
            for ancillary_variable in ancillary_variables:
                result_name = ('var', 'quality_variable', ancillary_variable.name, data_variable.name, 'check_listed')
                if ancillary_variable in self._quality_control_variables:
                    result = Result(BaseCheck.HIGH, True, result_name, None)
                else:
                    reasoning = ["Quality variable is not listed in the data variable's ancillary_variables attribute"]
                    result = Result(BaseCheck.HIGH, False, result_name, reasoning)

                ret_val.append(result)

        return ret_val

    def check_quality_control_variable_standard_name(self, ds):
        """
        Check quality control variable standard name attribute.
        """
        ret_val = []

        for qc_variable in self._quality_control_variables:
            for data_variable in self._data_variables:
                ancillary_variables = find_ancillary_variables_by_variable(ds.dataset, data_variable)
                if qc_variable in ancillary_variables:
                    value = getattr(data_variable, 'standard_name', '') + ' ' + 'status_flag'
                    result_name = ('var', 'quality_variable', qc_variable.name, data_variable.name, 'check_standard_name')
                    if getattr(qc_variable, 'standard_name', '') != value:
                        reasoning = ["Standard name is not correct"]
                        result = Result(BaseCheck.HIGH, False, result_name, reasoning)
                    else:
                        result = Result(BaseCheck.HIGH, True, result_name, None)

                    ret_val.append(result)
        return ret_val

    def check_geospatial_lat_units(self, ds):
        """
        Check geospatial_lat_units global attribute and the value is 'degrees_north,
        if exists
        """
        ret_val = []

        result_name = ('globalattr', 'geospatial_lat_units','check_attributes')

        result = self._check_value(("geospatial_lat_units",),
                                    "degrees_north",
                                    IMOSCheck.OPERATOR_EQUAL,
                                    ds,
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.MEDIUM,
                                    None,
                                    True)

        if result is not None:
            ret_val.append(result)

        return ret_val

    def check_geospatial_lon_units(self, ds):
        """
        Check geospatial_lon_units global attribute and the value is 'degrees_east',
        if exists
        """
        ret_val = []

        result_name = ('globalattr', 'geospatial_lon_units','check_attributes')

        result = self._check_value(("geospatial_lon_units",),
                                    "degrees_east",
                                    IMOSCheck.OPERATOR_EQUAL,
                                    ds,
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.MEDIUM,
                                    None,
                                    True)

        if result is not None:
            ret_val.append(result)

        return ret_val

    def check_geospatial_vertical_positive(self, ds):
        """
        Check geospatial_vertical_positive global attribute and the value is 'up' or 'down',
        if exists
        """        
        ret_val = []

        result_name = ('globalattr', 'geospatial_vertical_positive','check_attributes')

        result = self._check_present(("geospatial_vertical_positive",),
                            ds,
                            IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                            result_name,
                            BaseCheck.MEDIUM)

        if result.value:
            result1 = self._check_value(("geospatial_vertical_positive",),
                                    "up",
                                    IMOSCheck.OPERATOR_EQUAL,
                                    ds,
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.MEDIUM)

            result2 = self._check_value(("geospatial_vertical_positive",),
                                    "down",
                                    IMOSCheck.OPERATOR_EQUAL,
                                    ds,
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.MEDIUM)
            result = None
            reasoning = ["value is not equal to up or down"]
            if result1.value or result2.value:
                result = Result(BaseCheck.HIGH, True, result_name, None)
            else:
                result = Result(BaseCheck.HIGH, False, result_name, reasoning)

            ret_val.append(result)

        return ret_val

    def check_author_email(self, ds):
        """
        Check value of author_email global attribute is valid email address,
        if exists
        """
        ret_val = []

        result_name = ('globalattr', 'author_email','check_attributes')

        result = self._check_value(("author_email",),
                                    "",
                                    IMOSCheck.OPERATOR_EMAIL,
                                    ds,
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.MEDIUM,
                                    None,
                                    True)
        if result is not None:
            ret_val.append(result)

        return ret_val

    def check_principal_investigator_email(self, ds):
        """
        Check value of principal_investigator_email global attribute is valid email address,
        if exists
        """
        ret_val = []

        result_name = ('globalattr', 'principal_investigator_email','check_attributes')

        result = self._check_value(("principal_investigator_email",),
                                    "",
                                    IMOSCheck.OPERATOR_EMAIL,
                                    ds,
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.MEDIUM,
                                    None,
                                    True)
        if result is not None:
            ret_val.append(result)

        return ret_val

    def check_quality_control_set(self, ds):
        """
        Check value of quality_control_set global attribute is one of (1,2,3,4),
        if exists
        """
        ret_val = []

        result_name = ('globalattr', 'quality_control_set','check_attributes')

        result = self._check_value(("quality_control_set",),
                                    [1,2,3,4],
                                    IMOSCheck.OPERATOR_WITHIN,
                                    ds,
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.MEDIUM,
                                    None,
                                    True)
        if result is not None:
            ret_val.append(result)

        return ret_val
    
    def check_local_time_zone(self, ds):
        """
        Check value of local time zone global attribute is between -12 and 12,
        if exists
        """
        ret_val = []

        result_name = ('globalattr', 'local_time_zone','check_attributes')

        value = [i for i in range(-12, 13)]

        result = self._check_value(("local_time_zone",),
                                    value,
                                    IMOSCheck.OPERATOR_WITHIN,
                                    ds,
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.MEDIUM,
                                    None,
                                    True)
        if result is not None:
            ret_val.append(result)

        return ret_val

    def check_geospatial_vertical_units(self, ds):
        """
        Check value of lgeospatial_vertical_units global attribute is valid CF depth
        unit, if exists
        """
        ret_val = []
        result_name = ('var', 'geospatial_vertical_units','check_attributes')
        reasoning = ["units is not a valid CF depth unit"]

        result = self._check_value(('geospatial_vertical_units',),
                                        'meter',
                                        IMOSCheck.OPERATOR_CONVERTIBLE,
                                        ds,
                                        IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH,
                                        reasoning,
                                        True)

        if result is not None:
            ret_val.append(result)

        return ret_val
