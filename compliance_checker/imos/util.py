import numpy as np
import re

def is_monotonic(x):
    """
    Check whether an array is monotonic
    """
    dx = np.diff(x)
    return np.all(dx <= 0) or np.all(dx >= 0)

def is_valid_email(email):
    """Email validation, checks for syntactically invalid email"""

    emailregex = "^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3\})(\\]?)$"

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

def find_ancillary_variables_by_variable(dataset, variable):
    ancillary_variables = []
    ancillary_variable_names = getattr(variable, 'ancillary_variables', None)

    if ancillary_variable_names is not None:
        for ancillary_variable_name in ancillary_variable_names.split(' '):
            ancillary_variable = dataset.variables[ancillary_variable_name]
            ancillary_variables.append(ancillary_variable)

    return ancillary_variables

def find_ancillary_variables(dataset):
    ancillary_variables = []

    for name, var in dataset.variables.iteritems():
        ancillary_variables.extend(find_ancillary_variables_by_variable(dataset, var))

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

    for name, var in dataset.variables.iteritems():
        if var not in coordinate_variables and var not in ancillary_variables and var.dimensions:
            data_variables.append(var)

    return data_variables

def find_quality_control_variables(dataset):
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

        if getattr(var, 'flag_values', None) is not None or getattr(var, 'flag_meanings', None) is not None:
            quality_control_variables.append(var)
            continue

    return quality_control_variables
