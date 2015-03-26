#!/usr/bin/env python
'''
Compliance Test Suite for the Integrated Marine Observing System
http://www.imos.org.au/
'''

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
                result_name = ('globalattr', name,'check_attributes')
                reasoning = None
                if not attribute_value:
                    #empty global attribute
                    reasoning = ['Attribute value is empty']

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
                    result_name = ('var', variable_name, attribute_name,'check_attributes')
                    reasoning = None
                    if not attribute_value:
                        #empty variable attribute
                        reasoning = ['Attribute value is empty']

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

        global_attributes = ds.dataset.ncattrs()

        if 'project' not in global_attributes:
            reasoning = ['Attribute is not present']
            result = Result(BaseCheck.HIGH, False, result_name, reasoning)
            ret_val.append(result)
        else:
            attribute_value = getattr(ds.dataset, "project")
            if attribute_value != 'Integrated Marine Observing System (IMOS)':
                reasoning = ['Attribute value is not equal to Integrated Marine Observing System (IMOS)']
                result = Result(BaseCheck.HIGH, False, result_name, reasoning)
                ret_val.append(result)
            else:
                result = Result(BaseCheck.HIGH, True, result_name, None)

        return ret_val
