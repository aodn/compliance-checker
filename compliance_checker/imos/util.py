import numpy as np
import re

from compliance_checker.base import Result

CHECK_VARIABLE = 1
CHECK_GLOBAL_ATTRIBUTE = 0
CHECK_VARIABLE_ATTRIBUTE = 3


def is_monotonic(x):
    """
    Check whether an array is monotonic
    """
    dx = np.diff(x)
    return np.all(dx <= 0) or np.all(dx >= 0)

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
