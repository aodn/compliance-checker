''' Provide helper methods for IMOSChecker class
'''
import datetime

import numpy as np
import re

from numpy import amax
from numpy import amin


from compliance_checker.base import BaseCheck
from compliance_checker.base import Result
from compliance_checker.cf.util import units_convertible

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

def is_monotonic(array):
    """
    Check whether an array is monotonic
    """
    diff = np.diff(array)
    return np.all(diff <= 0) or np.all(diff >= 0)

def is_valid_email(email):
    """Email validation, checks for syntactically invalid email"""

    emailregex = \
        "^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3\})(\\]?)$"

    if re.match(emailregex, email) != None:
        return True

    return False

def is_numeric(variable_type):
    """
    Check whether a numpy type is numeric type (byte,
    float and integer)
    """
    if variable_type == np.double:
        return True

    if variable_type == np.integer:
        return True

    if variable_type == np.byte:
        return True

    if variable_type == np.float:
        return True

    return False

def find_variables_from_attribute(dataset, variable, attribute_name):
    ''' Get variables based on a variable attribure such as coordinates.
    '''
    variables = []
    variable_names = getattr(variable, attribute_name, None)

    if variable_names is not None:
        for variable_name in variable_names.split(' '):
            variable = dataset.variables[variable_name]
            variables.append(variable)

    return variables

def find_auxiliary_coordinate_variables(dataset):
    ''' Find all ancillary variables associated with a variable.
    '''
    auxiliary_coordinate_variables = []

    for name, var in dataset.variables.iteritems():
        auxiliary_coordinate_variables.extend(\
            find_variables_from_attribute(dataset, var, 'coordinates'))

    return auxiliary_coordinate_variables

def find_ancillary_variables_by_variable(dataset, variable):
    ''' Find all ancillary variables associated with a variable.
    '''
    ancillary_variables = []
    ancillary_variable_names = getattr(variable, 'ancillary_variables', None)

    if ancillary_variable_names is not None:
        for ancillary_variable_name in ancillary_variable_names.split(' '):
            ancillary_variable = dataset.variables[ancillary_variable_name]
            ancillary_variables.append(ancillary_variable)

    return ancillary_variables

def find_ancillary_variables(dataset):
    ''' Find all ancillary variables.
    '''
    ancillary_variables = []

    for name, var in dataset.variables.iteritems():
        ancillary_variables.extend(find_variables_from_attribute(dataset, var, \
                                     'ancillary_variables'))

    return ancillary_variables

def find_data_variables(dataset, coordinate_variables, ancillary_variables):
    """
        Finds all variables that could be considered Data variables.

        Returns a dictionary mapping name -> variable.

        Excludes variables that are:
            - coordinate variables
            - ancillary variables
            - no dimensions

        Results are NOT CACHED.
        """
    data_variables = []
    auxiliary_coordinate_variables = find_auxiliary_coordinate_variables(dataset)

    for name, var in dataset.variables.iteritems():
        if var not in coordinate_variables and var not in \
            ancillary_variables and var.dimensions and var not in \
            auxiliary_coordinate_variables:

            data_variables.append(var)

    return data_variables

def find_quality_control_variables(dataset):
    ''' Find all quality control variables in a given netcdf file
    '''
    quality_control_variables = []

    for name, var in dataset.variables.iteritems():
        if name.endswith('_quality_control'):
            quality_control_variables.append(var)
            continue

        standard_name = getattr(var, 'standard_name', None)
        if standard_name is not None and standard_name.endswith('status_flag'):
            quality_control_variables.append(var)
            continue

        long_name = getattr(var, 'long_name', None)
        if long_name is not None and isinstance(long_name, basestring):
            if 'status_flag' in long_name or 'quality flag' in long_name:
                quality_control_variables.append(var)
                continue

        if getattr(var, 'flag_values', None) is not None or getattr(var,\
                    'flag_meanings', None) is not None:
            quality_control_variables.append(var)
            continue

    return quality_control_variables

def check_present(name, data, check_type, result_name, check_priority, reasoning=None):
    """
    Help method to check whether a variable, variable attribute
    or a global attribute presents.

    params:
        name (tuple): variable name and attribute name.
                        For global attribute, only attribute name present.
        data (Dataset): netcdf data file
        check_type (int): CHECK_VARIABLE, CHECK_GLOBAL_ATTRIBUTE,
                        CHECK_VARIABLE_ATTRIBUTE
        result_name: the result name to display
        check_priority (int): the check priority
        reasoning (str): reason string for failed check
    return:
        result (Result): result for the check
    """
    passed = True

    if check_type == CHECK_GLOBAL_ATTRIBUTE:
        if not result_name:
            result_name = ('globalattr', name[0],'check_attribute_present')
        if name[0] not in data.dataset.ncattrs():
            if not reasoning:
                reasoning = ["Attribute is not present"]
                passed = False

    if check_type == CHECK_VARIABLE or\
        check_type == CHECK_VARIABLE_ATTRIBUTE:
        if not result_name:
            result_name = ('var', name[0],'check_variable_present')

        variable = data.dataset.variables.get(name[0], None)

        if variable == None:
            if not reasoning:
                reasoning = ['Variable is not present']
            passed = False

        else:
            if check_type == CHECK_VARIABLE_ATTRIBUTE:
                if not result_name:
                    result_name = ('var', name[0], name[1], 'check_variable_attribute_present')
                if name[1] not in variable.ncattrs():
                    if not reasoning:
                        reasoning = ["Variable attribute is not present"]
                    passed = False

    result = Result(check_priority, passed, result_name, reasoning)

    return result

def check_value(name, value, operator, ds, check_type, result_name, check_priority, reasoning=None, skip_check_presnet=False):
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
    result = check_present(name, ds, check_type,
                           result_name,
                           BaseCheck.HIGH)

    if result.value:
        result = None
        retrieved_value = None
        passed = True

        if check_type == CHECK_GLOBAL_ATTRIBUTE:
            retrieved_value = getattr(ds.dataset, name[0])

        if check_type == CHECK_VARIABLE:
            variable = ds.dataset.variables.get(name[0], None)

        if check_type == CHECK_VARIABLE_ATTRIBUTE:
            variable = ds.dataset.variables.get(name[0], None)
            retrieved_value = getattr(variable, name[1])

        if operator == OPERATOR_EQUAL:
            if retrieved_value != value:
                if not reasoning:
                    reasoning = ["Attribute value is not equal to " + str(value)]
                    passed = False

        if operator == OPERATOR_MIN:
            min_value = amin(variable.__array__())

            if min_value != float(value):
                passed = False
                if not reasoning:
                    reasoning = ["Minimum value is not same as the attribute value"]

        if operator == OPERATOR_MAX:
            max_value = amax(variable.__array__())
            if max_value != float(value):
                passed = False
                if not reasoning:
                    reasoning = ["Maximum value is not same as the attribute value"]

        if operator == OPERATOR_DATE_FORMAT:
            try:
                datetime.datetime.strptime(retrieved_value, value)
            except ValueError:
                passed = False
                if not reasoning:
                    reasoning = ["Datetime format is not correct"]

        if operator == OPERATOR_SUB_STRING:
            if value not in retrieved_value:
                passed = False
                if not reasoning:
                    reasoning = ["Required substring is not contained"]

        if operator == OPERATOR_CONVERTIBLE:
            if not units_convertible(retrieved_value, value):
                passed = False
                if not reasoning:
                    reasoning = ["Value is not convertible"]

        if operator == OPERATOR_EMAIL:
            if not is_valid_email(retrieved_value):
                passed = False
                if not reasoning:
                    reasoning = ["Value is not a valid email"]

        if operator == OPERATOR_WITHIN:
            if retrieved_value not in value:
                passed = False
                if not reasoning:
                    reasoning = ["Value is not in the expected range"]

        result = Result(BaseCheck.HIGH, passed, result_name, reasoning)

    else:
        if skip_check_presnet:
            result = None

    return result

def check_attribute_type(name, type, ds, check_type, result_name, check_priority, reasoning=None, skip_check_presnet=False):
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
    result = check_present(name, ds, check_type,
                           result_name,
                           BaseCheck.HIGH)

    if result.value:
        if check_type == CHECK_GLOBAL_ATTRIBUTE:
            attribute_value = getattr(ds.dataset, name[0])

        if check_type == CHECK_VARIABLE_ATTRIBUTE:
            attribute_value = getattr(ds.dataset.variables[name[0]], name[1])

        if check_type == CHECK_VARIABLE:
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
