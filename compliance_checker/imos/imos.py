#!/usr/bin/env python
'''
Compliance Test Suite for the Integrated Marine Observing System
http://www.imos.org.au/
'''

from numbers import Number
from numpy import amax
from numpy import amin
from compliance_checker.base import BaseCheck, BaseNCCheck, Result
 
class IMOSCheck(BaseNCCheck):

    CHECK_VARIABLE = 1
    CHECK_GLOBAL_ATTRIBUTE = 0
    CHECK_VARIABLE_ATTRIBUTE = 3
    
    OPERATOR_EQUAL = 1
    OPERATOR_MIN = 2
    OPERATOR_MAX = 3
    OPERATOR_WITHIN = 4

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
                pass

            if operator == IMOSCheck.OPERATOR_EQUAL:
                if retrieved_value != value:
                    if not reasoning:
                        reasoning = ["Attribute value is not equal to " + value]
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

            result = Result(BaseCheck.HIGH, passed, result_name, reasoning)

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
        result = self._check_present((name,), ds, IMOSCheck.CHECK_GLOBAL_ATTRIBUTE,
                            result_name,
                            BaseCheck.HIGH)

        if result.value:
            attribute_value = getattr(ds.dataset, name)

            if not isinstance(attribute_value, type):
                print "called"
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
        result_name = ('globalattr', 'geospatial_lat_min', 'check_attribute_type')
        result = self._check_attribute_type("geospatial_lat_min",
                                            Number,
                                            ds,
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
        result2 = self._check_attribute_type("geospatial_lat_max",
                                            Number,
                                            ds,
                                            result_name,
                                            BaseCheck.HIGH,
                                            ["Attribute type is not numeric"])
        if result2:
            ret_val.append(result2)

        if result2.value:
            geospatial_lat_max = getattr(ds.dataset, "geospatial_lat_max", None)
            result_name = ('globalattr', 'geospatial_lat_max','check_maximum_value')
            result = self._check_value(('LONGITUDE',),
                                       geospatial_lat_max,
                                       IMOSCheck.OPERATOR_MAX,
                                       ds,
                                       IMOSCheck.CHECK_VARIABLE,
                                       result_name,
                                       BaseCheck.HIGH)
            ret_val.append(result)

        return ret_val

