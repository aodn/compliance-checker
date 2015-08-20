#!/usr/bin/env python
'''
Compliance Test Suite for the Integrated Marine Observing System
http://www.imos.org.au/
'''

import datetime
from types import IntType

import numpy as np
from numpy import amax
from numpy import amin
import re

from compliance_checker.cf.util import find_coord_vars, _possibleaxis, _possibleaxisunits
from compliance_checker.base import BaseCheck, BaseNCCheck, Result

from compliance_checker.imos.util import is_monotonic
from compliance_checker.imos.util import is_numeric
from compliance_checker.imos.util import find_ancillary_variables
from compliance_checker.imos.util import find_data_variables
from compliance_checker.imos.util import find_quality_control_variables
from compliance_checker.imos.util import find_ancillary_variables_by_variable
from compliance_checker.imos.util import check_present
from compliance_checker.imos.util import check_value
from compliance_checker.imos.util import check_attribute_type


class IMOSCheck(BaseNCCheck):
    """This is the class implements the IMOS netcdf check logic
    """
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
        """ This is the method from parent class.
        """
        return {}

    def setup(self, dataset):
        """This method is called by parent class and initialization code should
        go here
        """
        self._coordinate_variables = find_coord_vars(dataset.dataset)
        self._ancillary_variables = find_ancillary_variables(dataset.dataset)

        self._data_variables = find_data_variables(dataset.dataset,\
                                self._coordinate_variables,\
                                self._ancillary_variables)

        self._quality_control_variables = find_quality_control_variables(dataset.dataset)

    def _check_str_type(self, dataset, name):
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
        result = check_attribute_type((name,),
                                      basestring,
                                      dataset,
                                      IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                      result_name,
                                      BaseCheck.HIGH,
                                      reasoning,
                                      False)
        ret_val.append(result)
        return ret_val

    def check_global_attributes(self, dataset):
        """
        Check to ensure all global string attributes are not empty.
        """
        ret_val = []
        result = None

        for name in dataset.dataset.ncattrs():
            attribute_value = getattr(dataset.dataset, name)
            if isinstance(attribute_value, basestring):
                result_name = ('globalattr', name,'check_attribute_empty')
                reasoning = None
                if not attribute_value:
                    #empty global attribute
                    reasoning = ["Attribute value is empty"]

                result = Result(BaseCheck.HIGH, reasoning == None, result_name, reasoning)
                ret_val.append(result)

        return ret_val

    def check_variable_attributes(self, dataset):
        """
        Check to ensure all variable string attributes are not empty.
        """
        ret_val = []
        result = None

        for variable_name, variable in dataset.dataset.variables.iteritems():
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

    def check_project_attribute(self, dataset):
        """
        Check the global project attribute and ensure it has value
        'Integrated Marine Observing System (IMOS)'
        """
        ret_val = []
        result_name = ('globalattr', 'project','check_attributes')

        result = check_value(("project",),
                                "Integrated Marine Observing System (IMOS)",
                                IMOSCheck.OPERATOR_EQUAL,
                                dataset,
                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                result_name,
                                BaseCheck.HIGH)

        ret_val.append(result)
        return ret_val

    def check_naming_authority(self, dataset):
        """
        Check the global naming authority attribute and ensure it has value 'IMOS'
        """
        ret_val = []
        result_name = ('globalattr', 'naming_authority','check_attributes')

        result = check_value(('naming_authority',),
                                "IMOS",
                                IMOSCheck.OPERATOR_EQUAL,
                                dataset,
                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                result_name,
                                BaseCheck.HIGH)

        ret_val.append(result)

        return ret_val

    def check_data_centre(self, dataset):
        """
        Check the global data centre attribute and ensure it has value
        'eMarine Information Infrastructure (eMII)'
        """
        ret_val = []
        result_name = ('globalattr', 'data_centre', 'check_attributes')
        result = check_value(('data_centre',),
                                "eMarine Information Infrastructure (eMII)",
                                IMOSCheck.OPERATOR_EQUAL,
                                dataset,
                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                result_name,
                                BaseCheck.HIGH)

        ret_val.append(result)
        return ret_val

    def check_author(self, dataset):
        """
        Check the global author attribute and ensure it is str type.
        """
        return self._check_str_type(dataset, "author")

    def check_geospatial_lat_min_max(self, dataset):
        """
        Check the global geospatial_lat_min and geospatial_lat_max attributes
        match range in data and numeric type
        """
        ret_val = []

        result_name = ('globalattr', 'geospatial_lat_min', 'check_attribute_type')
        result = check_present(('LATITUDE',), dataset, IMOSCheck.CHECK_VARIABLE,
                                result_name,
                                BaseCheck.HIGH)

        if result.value:
            result_name = ('globalattr', 'geospatial_lat_min', 'check_attribute_type')
            result = check_attribute_type(('geospatial_lat_min',),
                                        np.number,
                                        dataset,
                                        IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH,
                                        ["Attribute type is not numeric"])

            if result:
                ret_val.append(result)

            if result.value:
                geospatial_lat_min = getattr(dataset.dataset, "geospatial_lat_min", None)
                result_name = ('globalattr', 'geospatial_lat_min','check_minimum_value')
                result = check_value(('LATITUDE',),
                                        geospatial_lat_min,
                                        IMOSCheck.OPERATOR_MIN,
                                        dataset,
                                        IMOSCheck.CHECK_VARIABLE,
                                        result_name,
                                        BaseCheck.HIGH)
                ret_val.append(result)

            result_name = ('globalattr', 'geospatial_lat_max', 'check_attribute_type')
            result2 = check_attribute_type(('geospatial_lat_max',),
                                            np.number,
                                            dataset,
                                            IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                            result_name,
                                            BaseCheck.HIGH,
                                            ["Attribute type is not numeric"])
            if result2:
                ret_val.append(result2)

            if result2.value:
                geospatial_lat_max = getattr(dataset.dataset, "geospatial_lat_max", None)
                result_name = ('globalattr', 'geospatial_lat_max','check_maximum_value')
                result = check_value(('LATITUDE',),
                                        geospatial_lat_max,
                                        IMOSCheck.OPERATOR_MAX,
                                        dataset,
                                        IMOSCheck.CHECK_VARIABLE,
                                        result_name,
                                        BaseCheck.HIGH)
                ret_val.append(result)

        return ret_val

    def check_geospatial_lon_min_max(self, dataset):
        """
        Check the global geospatial_lon_min and geospatial_lon_max attributes
        match range in data and numeric type
        """
        ret_val = []

        result_name = ('globalattr', 'geospatial_lon_min', 'check_attribute_type')
        result = check_present(('LONGITUDE',), dataset, IMOSCheck.CHECK_VARIABLE,
                                result_name,
                                BaseCheck.HIGH)

        if result.value:
            result_name = ('globalattr', 'geospatial_lon_min', 'check_attribute_type')
            result = check_attribute_type(('geospatial_lon_min',),
                                            np.number,
                                            dataset,
                                            IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                            result_name,
                                            BaseCheck.HIGH,
                                            ["Attribute type is not numeric"])

            if result:
                ret_val.append(result)

            if result.value:
                geospatial_lon_min = getattr(dataset.dataset, "geospatial_lon_min", None)
                result_name = ('globalattr', 'geospatial_lon_min','check_minimum_value')
                result = check_value(('LONGITUDE',),
                                       geospatial_lon_min,
                                       IMOSCheck.OPERATOR_MIN,
                                       dataset,
                                       IMOSCheck.CHECK_VARIABLE,
                                       result_name,
                                       BaseCheck.HIGH)
                ret_val.append(result)

            result_name = ('globalattr', 'geospatial_lon_max', 'check_attribute_type')
            result2 = check_attribute_type(('geospatial_lon_max',),
                                            np.number,
                                            dataset,
                                            IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                            result_name,
                                            BaseCheck.HIGH,
                                            ["Attribute type is not numeric"])
            if result2:
                ret_val.append(result2)

            if result2.value:
                geospatial_lon_max = getattr(dataset.dataset, "geospatial_lon_max", None)
                result_name = ('globalattr', 'geospatial_lon_max','check_maximum_value')
                result = check_value(('LONGITUDE',),
                                       geospatial_lon_max,
                                       IMOSCheck.OPERATOR_MAX,
                                       dataset,
                                       IMOSCheck.CHECK_VARIABLE,
                                       result_name,
                                       BaseCheck.HIGH)
                ret_val.append(result)

        return ret_val

    def check_geospatial_vertical_min_max(self, dataset):
        """
        Check the global geospatial_vertical_min and
        geospatial_vertical_max attributes match range in data and numeric type
        """
        ret_val = []

        result_name = ('globalattr', 'geospatial_vertical_min', 'check_attribute_type')
        result = check_present(('VERTICAL',), dataset, IMOSCheck.CHECK_VARIABLE,
                                result_name,
                                BaseCheck.HIGH)

        if result.value:
            result_name = ('globalattr', 'geospatial_vertical_min', 'check_attribute_type')
            result = check_attribute_type(('geospatial_vertical_min',),
                                            np.number,
                                            dataset,
                                            IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                            result_name,
                                            BaseCheck.HIGH,
                                            ["Attribute type is not numeric"])

            if result:
                ret_val.append(result)

            if result.value:
                geospatial_vertical_min = getattr(dataset.dataset, "geospatial_vertical_min", None)
                result_name = ('globalattr', 'geospatial_vertical_min','check_minimum_value')
                result = check_value(('VERTICAL',),
                                       geospatial_vertical_min,
                                       IMOSCheck.OPERATOR_MIN,
                                       dataset,
                                       IMOSCheck.CHECK_VARIABLE,
                                       result_name,
                                       BaseCheck.HIGH)
                ret_val.append(result)

            result_name = ('globalattr', 'geospatial_vertical_max', 'check_attribute_type')
            result2 = check_attribute_type(('geospatial_vertical_max',),
                                            np.number,
                                            dataset,
                                            IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                            result_name,
                                            BaseCheck.HIGH,
                                            ["Attribute type is not numeric"])
            if result2:
                ret_val.append(result2)

            if result2.value:
                geospatial_vertical_max = getattr(dataset.dataset, "geospatial_vertical_max", None)
                result_name = ('globalattr', 'geospatial_vertical_max','check_maximum_value')
                result = check_value(('VERTICAL',),
                                       geospatial_vertical_max,
                                       IMOSCheck.OPERATOR_MAX,
                                       dataset,
                                       IMOSCheck.CHECK_VARIABLE,
                                       result_name,
                                       BaseCheck.HIGH)
                ret_val.append(result)

        return ret_val

    def check_time_coverage(self, dataset):
        """
        Check the global attributes time_coverage_start/time_coverage_end whether
        match format 'YYYY-MM-DDThh:mm:ssZ'
        """
        ret_val = []
        result_name = ('globalattr', 'time_coverage_start','check_date_format')

        result = check_present(('TIME',), dataset, IMOSCheck.CHECK_VARIABLE,
                                result_name,
                                BaseCheck.HIGH)

        if result.value:
            results = self._check_str_type(dataset, 'time_coverage_start')
            result = results[0]
            if result.value:
                result_name = ('globalattr', 'time_coverage_start','check_date_format')
                result = check_value(('time_coverage_start',),
                                    '%Y-%m-%dT%H:%M:%SZ',
                                    IMOSCheck.OPERATOR_DATE_FORMAT,
                                    dataset,
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)
            ret_val.append(result)

            results = self._check_str_type(dataset, 'time_coverage_end')
            result = results[0]
            if result.value:
                result_name = ('globalattr', 'time_coverage_end','check_date_format')
                result = check_value(('time_coverage_end',),
                                    '%Y-%m-%dT%H:%M:%SZ',
                                    IMOSCheck.OPERATOR_DATE_FORMAT,
                                    dataset,
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)
            ret_val.append(result)

        return ret_val

    def check_title(self, dataset):
        """
        Check the global attributes title has string type
        """
        return self._check_str_type(dataset, "title")

    def check_date_created(self, dataset):
        """
        Check the global attributes date_created whether
        match format 'YYYY-MM-DDThh:mm:ssZ'
        """
        ret_val = []

        results = self._check_str_type(dataset, 'date_created')
        result = results[0]
        if result.value:
            result_name = ('globalattr', 'date_created','check_date_format')
            result = check_value(('date_created',),
                                 '%Y-%m-%dT%H:%M:%SZ',
                                 IMOSCheck.OPERATOR_DATE_FORMAT,
                                 dataset,
                                 IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                 result_name,
                                 BaseCheck.HIGH)
        ret_val.append(result)

        return ret_val

    def check_abstract(self, dataset):
        """
        Check the global attributes abstract has string type
        """
        return self._check_str_type(dataset, "abstract")

    def _check_global_value_equal(self, dataset, name, value):
        """
        Check global attribute to has the required value.

        params:
            name (str): attribute name
        return:
            result (list): a list of Result objects

        """
        ret_val = []
        result_name = ('globalattr', name,'check_attributes')

        result = check_value((name,),
                                value,
                                IMOSCheck.OPERATOR_EQUAL,
                                dataset,
                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                result_name,
                                BaseCheck.HIGH)

        ret_val.append(result)

        return ret_val

    def check_data_centre_email(self, dataset):
        """
        Check the global data_centre_email and ensure it has value 'info@emii.org.au'
        """
        return self._check_global_value_equal(dataset,'data_centre_email', 'info@emii.org.au')

    def check_principal_investigator(self, dataset):
        '''
        Check the global attribute principal_investigator
        '''
        return self._check_str_type(dataset, 'principal_investigator')

    def check_citation(self, dataset):
        '''
        Check the global attribute citation
        '''
        return self._check_str_type(dataset, 'citation')

    def check_acknowledgement(self, dataset):
        """
        Check the global acknowledgement attribute and ensure it contains the
        required text.
        """
        ret_val = []
        old_pattern = ".*Any users of IMOS data are required to clearly" \
                      " acknowledge the source of the material in the format:" \
                      ".*" \
                      "Data was sourced from the Integrated Marine Observing" \
                      " System \(IMOS\) - IMOS is supported by the Australian" \
                      " Government through the National Collaborative Research" \
                      " Infrastructure Strategy \(NCRIS\) and the Super" \
                      " Science Initiative \(SSI\)"
        new_pattern = ".*Any users of IMOS data are required to clearly" \
                      " acknowledge the source of the material derived from" \
                      " IMOS in the format:" \
                      ".*" \
                      "Data was sourced from the Integrated Marine Observing" \
                      " System \(IMOS\) - IMOS is a national collaborative" \
                      " research infrastructure," \
                      " supported by the Australian Government"

        acknowledgement = getattr(dataset.dataset, 'acknowledgement', None)

        # check the attribute is present
        present = True
        reasoning = None
        if acknowledgement is None:
            present = False
            reasoning = ['Missing global attribute acknowledgement']
        result_name = ('globalattr', 'acknowledgement', 'present')
        result = Result(BaseCheck.HIGH, present, result_name, reasoning)

        ret_val.append(result)

        # skip the rest if attribute not there
        if not result.value:
            return ret_val

        # test whether old or new substrings match the attribute value
        passed = False
        reasoning = ["acknowledgement string doesn't contain the required text"]
        if re.match(old_pattern, acknowledgement) or \
           re.match(new_pattern, acknowledgement):
            passed = True
            reasoning = None
        result_name = ('globalattr', 'acknowledgement', 'value')
        result = Result(BaseCheck.HIGH, passed, result_name, reasoning)

        ret_val.append(result)

        return ret_val

    def check_distribution_statement(self, dataset):
        """
        Check the global distribution statement attribute and ensure it has
        expected value
        """
        result_name = ('globalattr', 'distribution_statement','check_attributes')
        value = 'Data may be re-used, provided that related metadata explaining' \
        ' the data has been reviewed by the user, and the data is appropriately' \
        ' acknowledged. Data, products and services from IMOS are' \
        ' provided "as is" without any warranty as to fitness for a' \
        ' particular purpose.'

        ret_val = []
        result = check_value(('distribution_statement',),
                                value,
                                IMOSCheck.OPERATOR_SUB_STRING,
                                dataset,
                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                result_name,
                                BaseCheck.HIGH)
        ret_val.append(result)

        return ret_val

    def check_variables_long_name(self, dataset):
        """
        Check the every variable long name attribute and ensure it is string type.
        """
        ret_val = []
        for name, var in dataset.dataset.variables.iteritems():
            result_name = ('var', name, 'long_name', 'check_atttribute_type')
            reasoning = ["Attribute type is not string"]

            result = check_attribute_type((name,'long_name',),
                                             basestring,
                                             dataset,
                                             IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                             result_name,
                                             BaseCheck.HIGH,
                                             reasoning)
            ret_val.append(result)

        return ret_val

    def check_coordinate_variables(self, dataset):
        """
        Check all coordinate variables to ensure it has numeric type (byte,
        float and integer) and also check whether it is monotonic
        """

        space_time_checked = False

        ret_val = []
        for var in self._coordinate_variables:
            result_name = ('var', 'coordinate_variable', var.name, 'check_variable_type')
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

            result_name = ('var', 'coordinate_variable', var.name, 'space_time_coordinate', 'check_variable_present')
            passed = False
            reasoning = None

            if str(var.name) in _possibleaxis \
                or (hasattr(var, 'units') and (var.units in _possibleaxisunits or var.units.split(" ")[0]  in _possibleaxisunits)) \
                or hasattr(var,'positive'):
                space_time_checked = True

            reasoning = ["No space-time coordinate variable found"]

            result = Result(BaseCheck.HIGH, space_time_checked, result_name, reasoning)
            ret_val.append(result)

        return ret_val

    def check_time_variable(self, dataset):
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
        result = check_present(('TIME',),
                                dataset,
                                IMOSCheck.CHECK_VARIABLE,
                                result_name,
                                BaseCheck.HIGH)
        if result.value:

            result_name = ('var', 'TIME', 'standard_name', 'check_attributes')

            result = check_value(('TIME','standard_name',),
                                    'time',
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'TIME', 'axis', 'check_attributes')

            result = check_value(('TIME','axis',),
                                    'T',
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'TIME', 'valid_min', 'check_present')

            result = check_present(('TIME', 'valid_min'),
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'TIME', 'valid_max', 'check_present')

            result = check_present(('TIME', 'valid_max'),
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'TIME', 'calendar', 'check_attribute_value')

            result = check_value(('TIME','calendar',),
                                    'gregorian',
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'TIME','check_variable_type')
            reasoning = ["The Type of variable TIME is not Double"]

            result = check_attribute_type(('TIME',),
                                        np.float64,
                                        dataset,
                                        IMOSCheck.CHECK_VARIABLE,
                                        result_name,
                                        BaseCheck.HIGH,
                                        reasoning)

            ret_val.append(result)

            result_name = ('var', 'TIME', 'units', 'check_attribute_value')
            reasoning = ["The TIME attribute units doesn't match the IMOS recommended units 'days since 1950-01-01 00:00:00 UTC'"]

            result = check_value(('TIME','units',),
                                    'days since 1950-01-01 00:00:00 UTC',
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.MEDIUM,
                                    reasoning)

            ret_val.append(result)

        return ret_val

    def check_longitude_variable(self, dataset):
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
        result = check_present(('LONGITUDE',),
                                dataset,
                                IMOSCheck.CHECK_VARIABLE,
                                result_name,
                                BaseCheck.HIGH)

        if result.value:
            result_name = ('var', 'LONGITUDE', 'standard_name', 'check_attributes')

            result = check_value(('LONGITUDE','standard_name',),
                                    'longitude',
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'LONGITUDE', 'axis', 'check_attributes')

            result = check_value(('LONGITUDE','axis',),
                                    'X',
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'LONGITUDE', 'reference_datum', 'check_attributes')
            result = check_attribute_type(('LONGITUDE','reference_datum',),
                                    basestring,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            ret_val.append(result)

            result1 = check_value(('LONGITUDE','valid_min',),
                                    0,
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            result2 = check_value(('LONGITUDE','valid_max',),
                                    360,
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            result3 = check_value(('LONGITUDE','valid_min',),
                                    -180,
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            result4 = check_value(('LONGITUDE','valid_max',),
                                    180,
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
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
                if 'present' in result1.msgs[0]:
                    result_name = ('var', 'LONGITUDE', 'valid_min', 'check_min_value')
                    reasoning = ["Variable attribute is not present"]
                    result = Result(BaseCheck.HIGH, False, result_name, reasoning)
                    ret_val.append(result)
                elif not result1.value:
                    result_name = ('var', 'LONGITUDE', 'valid_min', 'check_min_value')
                    reasoning = ["doesn't match value pair (0, 360) or (-180, 180)"]
                    result = Result(BaseCheck.HIGH, False, result_name, reasoning)
                    ret_val.append(result)

                if 'present' in result2.msgs[0]:
                    result_name = ('var', 'LONGITUDE', 'valid_max', 'check_max_value')
                    reasoning = ["Variable attribute is not present"]
                    result = Result(BaseCheck.HIGH, False, result_name, reasoning)
                    ret_val.append(result)
                elif not result2.value:
                    result_name = ('var', 'LONGITUDE', 'valid_max', 'check_max_value')
                    reasoning = ["doesn't match value pair (0, 360) or (-180, 180)"]
                    result = Result(BaseCheck.HIGH, False, result_name, reasoning)
                    ret_val.append(result)

            result_name = ('var', 'LONGITUDE', 'units', 'check_attribute_value')
            result = check_value(('LONGITUDE','units',),
                                    'degrees_east',
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'LONGITUDE','check_variable_type')
            reasoning = ["The Type of variable LONGITUDE is not Double or Float"]

            result = check_attribute_type(('LONGITUDE',),
                                        [np.float64, np.float, np.float32, np.float16, np.float128],
                                        dataset,
                                        IMOSCheck.CHECK_VARIABLE,
                                        result_name,
                                        BaseCheck.HIGH,
                                        reasoning)

            ret_val.append(result)

        return ret_val

    def check_latitude_variable(self, dataset):
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


        result = check_present(('LATITUDE',),
                                dataset,
                                IMOSCheck.CHECK_VARIABLE,
                                result_name,
                                BaseCheck.HIGH)

        if result.value:
            result = check_value(('LATITUDE','standard_name',),
                                    'latitude',
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'LATITUDE', 'axis', 'check_attributes')

            result = check_value(('LATITUDE','axis',),
                                    'Y',
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'LATITUDE', 'reference_datum', 'check_attributes')
            result = check_attribute_type(('LATITUDE','reference_datum',),
                                    basestring,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'LATITUDE', 'valid_min', 'check_min_value')
            result = check_value(('LATITUDE','valid_min',),
                                    -90,
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)
            ret_val.append(result)

            result_name = ('var', 'LATITUDE', 'valid_max', 'check_max_value')
            result = check_value(('LATITUDE','valid_max',),
                                    90,
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)
            ret_val.append(result)

            result_name = ('var', 'LATITUDE', 'units', 'check_attribute_value')
            result = check_value(('LATITUDE','units',),
                                        'degrees_north',
                                        IMOSCheck.OPERATOR_EQUAL,
                                        dataset,
                                        IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                        result_name,
                                        BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'LATITUDE','check_variable_type')
            reasoning = ["The Type of variable LATITUDE is not Double or Float"]

            result = check_attribute_type(('LATITUDE',),
                                            [np.float64, np.float, np.float32, np.float16, np.float128],
                                            dataset,
                                            IMOSCheck.CHECK_VARIABLE,
                                            result_name,
                                            BaseCheck.HIGH,
                                            reasoning)

            ret_val.append(result)

        return ret_val

    def check_vertical_variable(self, dataset):
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
        result = check_present(('VERTICAL',),
                                dataset,
                                IMOSCheck.CHECK_VARIABLE,
                                result_name,
                                BaseCheck.HIGH)
        if result.value:

            result_name = ('var', 'VERTICAL', 'reference_datum', 'check_attributes')
            result = check_attribute_type(('VERTICAL','reference_datum',),
                                       basestring,
                                       dataset,
                                       IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                       result_name,
                                       BaseCheck.HIGH)

            ret_val.append(result)

            result1 = check_value(('VERTICAL','standard_name',),
                              'depth',
                              IMOSCheck.OPERATOR_EQUAL, dataset,
                              IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                              result_name,
                              BaseCheck.HIGH)

            result2 = check_value(('VERTICAL','standard_name',),
                              'height',
                              IMOSCheck.OPERATOR_EQUAL, dataset,
                              IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                              result_name,
                              BaseCheck.HIGH)

            result3 = check_value(('VERTICAL','positive',),
                              'down',
                              IMOSCheck.OPERATOR_EQUAL, dataset,
                              IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                              result_name,
                              BaseCheck.HIGH)

            result4 = check_value(('VERTICAL','positive',),
                              'up',
                              IMOSCheck.OPERATOR_EQUAL, dataset,
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

            result = check_present(('VERTICAL', 'valid_min'),
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'VERTICAL', 'valid_max', 'check_present')

            result = check_present(('VERTICAL', 'valid_max'),
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'VERTICAL', 'axis', 'check_attributes')

            result = check_value(('VERTICAL','axis',),
                                    'Z',
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH)

            ret_val.append(result)

            result_name = ('var', 'VERTICAL', 'units', 'check_attributes')
            reasoning = ["units is not a valid CF distance unit"]
            result = check_value(('VERTICAL','units',),
                                    'meter',
                                    IMOSCheck.OPERATOR_CONVERTIBLE,
                                    dataset,
                                    IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH,
                                    reasoning)

            ret_val.append(result)

            result_name = ('var', 'VERTICAL','check_variable_type')
            reasoning = ["The Type of variable VERTICAL is not Double or Float"]

            result = check_attribute_type(('VERTICAL',),
                                        [np.float64, np.float, np.float32, np.float16, np.float128],
                                        dataset,
                                        IMOSCheck.CHECK_VARIABLE,
                                        result_name,
                                        BaseCheck.HIGH,
                                        reasoning)

            ret_val.append(result)

        return ret_val

    def check_variable_attribute_type(self, dataset):
        """
        Check variable attribute to ensure it has the same type as the variable
        """

        ret_val = []
        reasoning = ["Attribute type is not same as variable type"]
        for name,var in dataset.dataset.variables.iteritems():
            result_name = ('var', name, '_FillValue', 'check_attribute_type')
            result = check_attribute_type((name,'_FillValue',),
                                            var.datatype,
                                            dataset,
                                            IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                            result_name,
                                            BaseCheck.HIGH,
                                            reasoning,
                                            True)
            if not result is None:
                ret_val.append(result)

            result_name = ('var', name, 'valid_min', 'check_attribute_type')

            result = check_attribute_type((name,'valid_min',),
                                            var.datatype,
                                            dataset,
                                            IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                            result_name,
                                            BaseCheck.HIGH,
                                            reasoning,
                                            True)
            if not result is None:
                ret_val.append(result)

            result_name = ('var', name, 'valid_max', 'check_attribute_type')            
            result = check_attribute_type((name,'valid_max',),
                                                var.datatype,
                                                dataset,
                                                IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                                result_name,
                                                BaseCheck.HIGH,
                                                reasoning,
                                                True)
            if not result is None:
                ret_val.append(result)

        return ret_val

    def check_data_variables(self, dataset):
        """
        Check data variable:
            at least one data variable exists in the file
            variable has at least one spatial or temporal dimension
            attribute _FillValue exists
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
                # check for spatial/temporal dimension
                result_name = ('var', 'data_variable', var.name, 'check_dimension')
                passed = False
                reasoning = ["data variable should have at least one of the dimensions TIME, LATITUDE, LONGITUDE, DEPTH"]
                for dimension in var.dimensions:
                    if dimension in required_dimensions:
                        passed = True
                        reasoning = None
                        break
                result = Result(BaseCheck.HIGH, passed, result_name, reasoning)
                ret_val.append(result)

                # check that _FillValue attribute exists
                result_name = ('var', 'data_variable', var.name, '_FillValue')
                reasoning = None
                passed = hasattr(var, '_FillValue')
                if not passed:
                    reasoning = ["%s has no _FillValue attribute." % var.name]
                result = Result(BaseCheck.HIGH, passed, result_name, reasoning)
                ret_val.append(result)

        return ret_val

    def check_quality_control_set_for_quality_control_variable(self, dataset):
        """
        Check value of quality_control_set attribute is one of (1,2,3,4),
        for quality control variables
        """
        ret_val = []

        for qc_variable in self._quality_control_variables:
            result_name = ('var', 'quality_variable', qc_variable.name, 'quality_control_set', 'check_attributes')
            result = check_value((qc_variable.name,'quality_control_set',),
                                [1,2,3,4],
                                IMOSCheck.OPERATOR_WITHIN,
                                dataset,
                                IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                result_name,
                                BaseCheck.MEDIUM)

            if result is not None:
                ret_val.append(result)

        return ret_val

    def check_quality_control_conventions_for_quality_control_variable(self, dataset):
        """
        Check value of quality_control_conventions attribute matches
        the quality_control_set attribute
        """

        test_value_dict = {'1': "IMOS standard set using the IODE flags",\
                           '2': "ARGO quality control procedure",\
                           '3': "BOM (SST and Air-Sea flux) quality control procedure",\
                           '4': "WOCE quality control procedure" \
                            " (Multidisciplinary Underway Network - CO 2 measurements)"}

        ret_val = []

        for qc_variable in self._quality_control_variables:
            quality_control_set = getattr(qc_variable, 'quality_control_set', None)
            result_name = ('var', 'quality_variable', qc_variable.name,\
                            'quality_control_conventions', 'check_attributes')

            if quality_control_set is not None:
                key = str(int(qc_variable.quality_control_set))

                if key in test_value_dict:
                    test_value = test_value_dict[key]

                    reasoning = ["quality_control_conventions doesn't match" \
                                 " value in quality_control_set"]

                    result = check_value((qc_variable.name,'quality_control_conventions',),
                                            test_value,
                                            IMOSCheck.OPERATOR_EQUAL,
                                            dataset,
                                            IMOSCheck.CHECK_VARIABLE_ATTRIBUTE,
                                            result_name,
                                            BaseCheck.MEDIUM,
                                            reasoning)

                    if result is not None:
                        ret_val.append(result)
            else:
                reasoning = ["Variable attribute is not present"]
                result = Result(BaseCheck.HIGH, False, result_name, reasoning)
                ret_val.append(result)

        return ret_val

    def check_quality_control_variable_dimensions(self, dataset):
        """
        Check quality variable has same dimensions as the related data variable.
        """
        ret_val = []
        for qc_variable in self._quality_control_variables:
            for data_variable in self._data_variables:
                ancillary_variables = \
                find_ancillary_variables_by_variable(dataset.dataset, data_variable)
                if qc_variable in ancillary_variables:
                    result_name = ('var', 'quality_variable', qc_variable.name,\
                                    data_variable.name, 'check_dimension')
                    if data_variable.dimensions == qc_variable.dimensions:
                        result = Result(BaseCheck.HIGH, True, result_name, None)
                    else:
                        reasoning = ["Dimension is not same"]
                        result = Result(BaseCheck.HIGH, False, result_name, reasoning)

                    ret_val.append(result)

        return ret_val

    def check_quality_control_variable_listed(self, dataset):
        """
        Check quality control variable is listed in the related data variable's
        ancillary_variables attribute.
        """
        ret_val = []

        for quality_var in self._quality_control_variables:
            result_name = ('var', 'quality_variable', quality_var.name, 'check_listed')

            if quality_var in self._ancillary_variables:
                result = Result(BaseCheck.MEDIUM, True, result_name, None)
            else:
                reasoning = ["Quality variable is not listed in any data" \
                             " variable's ancillary_variables attribute"]
                result = Result(BaseCheck.MEDIUM, False, result_name, reasoning)

            ret_val.append(result)

        return ret_val

    def check_quality_control_variable_standard_name(self, ds):
        """
        Check quality control variable standard name attribute.
        """
        ret_val = []

        for qc_variable in self._quality_control_variables:
            for data_variable in self._data_variables:
                ancillary_variables = find_ancillary_variables_by_variable(
                                        ds.dataset, data_variable)
                if qc_variable in ancillary_variables:
                    value = getattr(data_variable, 'standard_name', '') + ' ' + 'status_flag'
                    result_name = ('var', 'quality_variable', qc_variable.name,\
                                    data_variable.name, 'check_standard_name')
                    if getattr(qc_variable, 'standard_name', '') != value:
                        reasoning = ["Standard name is not correct"]
                        result = Result(BaseCheck.HIGH, False, result_name, reasoning)
                    else:
                        result = Result(BaseCheck.HIGH, True, result_name, None)

                    ret_val.append(result)
        return ret_val

    def check_geospatial_lat_units(self, dataset):
        """
        Check geospatial_lat_units global attribute and the value is 'degrees_north,
        if exists
        """
        ret_val = []

        result_name = ('globalattr', 'geospatial_lat_units','check_attributes')

        result = check_value(("geospatial_lat_units",),
                                "degrees_north",
                                IMOSCheck.OPERATOR_EQUAL,
                                dataset,
                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                result_name,
                                BaseCheck.MEDIUM,
                                None,
                                True)

        if result is not None:
            ret_val.append(result)

        return ret_val

    def check_geospatial_lon_units(self, dataset):
        """
        Check geospatial_lon_units global attribute and the value is 'degrees_east',
        if exists
        """
        ret_val = []

        result_name = ('globalattr', 'geospatial_lon_units','check_attributes')

        result = check_value(("geospatial_lon_units",),
                                "degrees_east",
                                IMOSCheck.OPERATOR_EQUAL,
                                dataset,
                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                result_name,
                                BaseCheck.MEDIUM,
                                None,
                                True)

        if result is not None:
            ret_val.append(result)

        return ret_val

    def check_geospatial_vertical_positive(self, dataset):
        """
        Check geospatial_vertical_positive global attribute and the value is 'up' or 'down',
        if exists
        """
        ret_val = []

        result_name = ('globalattr', 'geospatial_vertical_positive','check_attributes')

        result = check_present(("geospatial_vertical_positive",),
                               dataset,
                               IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                               result_name,
                               BaseCheck.MEDIUM)

        if result.value:
            result1 = check_value(("geospatial_vertical_positive",),
                                "up",
                                IMOSCheck.OPERATOR_EQUAL,
                                dataset,
                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                result_name,
                                BaseCheck.MEDIUM)

            result2 = check_value(("geospatial_vertical_positive",),
                                    "down",
                                    IMOSCheck.OPERATOR_EQUAL,
                                    dataset,
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

    def check_author_email(self, dataset):
        """
        Check value of author_email global attribute is valid email address,
        if exists
        """
        ret_val = []

        result_name = ('globalattr', 'author_email','check_attributes')

        result = check_value(("author_email",),
                                "",
                                IMOSCheck.OPERATOR_EMAIL,
                                dataset,
                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                result_name,
                                BaseCheck.MEDIUM,
                                None,
                                True)

        if result is not None:
            ret_val.append(result)

        return ret_val

    def check_principal_investigator_email(self, dataset):
        """
        Check value of principal_investigator_email global attribute is valid email address,
        if exists
        """
        ret_val = []

        result_name = ('globalattr', 'principal_investigator_email','check_attributes')

        result = check_value(("principal_investigator_email",),
                                "",
                                IMOSCheck.OPERATOR_EMAIL,
                                dataset,
                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                result_name,
                                BaseCheck.MEDIUM,
                                None,
                                True)
        if result is not None:
            ret_val.append(result)

        return ret_val

    def check_quality_control_set(self, dataset):
        """
        Check value of quality_control_set global attribute is one of (1,2,3,4),
        if exists
        """
        ret_val = []

        result_name = ('globalattr', 'quality_control_set','check_attributes')

        result = check_value(("quality_control_set",),
                                [1,2,3,4],
                                IMOSCheck.OPERATOR_WITHIN,
                                dataset,
                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                result_name,
                                BaseCheck.MEDIUM,
                                None,
                                True)
        if result is not None:
            ret_val.append(result)

        return ret_val

    def check_local_time_zone(self, dataset):
        """
        Check value of local time zone global attribute is between -12 and 12,
        if exists
        """
        ret_val = []

        result_name = ('globalattr', 'local_time_zone','check_attributes')

        value = [i * 0.5 for i in range(-24, int(13 / 0.5)) if i <= 24]

        result = check_value(("local_time_zone",),
                                value,
                                IMOSCheck.OPERATOR_WITHIN,
                                dataset,
                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                result_name,
                                BaseCheck.MEDIUM,
                                None,
                                True)
        if result is not None:
            ret_val.append(result)

        return ret_val

    def check_geospatial_vertical_units(self, dataset):
        """
        Check value of lgeospatial_vertical_units global attribute is valid CF depth
        unit, if exists
        """
        ret_val = []
        result_name = ('var', 'geospatial_vertical_units','check_attributes')
        reasoning = ["units is not a valid CF depth unit"]

        result = check_value(('geospatial_vertical_units',),
                                    'meter',
                                    IMOSCheck.OPERATOR_CONVERTIBLE,
                                    dataset,
                                    IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                    result_name,
                                    BaseCheck.HIGH,
                                    reasoning,
                                    True)

        if result is not None:
            ret_val.append(result)

        return ret_val

    def check_conventions(self, ds):
        """
        Check the global Conventions attribute and ensure it contains value
        CF-1.6 and IMOS-1.3.
        """
        ret_val = []

        result_name = ('globalattr', 'Conventions','check_attributes')

        result1 = check_value(('Conventions',),
                                "CF-1.6",
                                IMOSCheck.OPERATOR_SUB_STRING,
                                ds,
                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                result_name,
                                BaseCheck.HIGH)

        ret_val.append(result1)
        result2 = check_value(('Conventions',),
                                "IMOS-1.3",
                                IMOSCheck.OPERATOR_SUB_STRING,
                                ds,
                                IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                                result_name,
                                BaseCheck.HIGH)

        ret_val.append(result2)
        return ret_val
