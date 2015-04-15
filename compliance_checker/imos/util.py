import numpy as np

def is_monotonic(x):
    """
    Check whether an array is monotonic
    """
    dx = np.diff(x)
    return np.all(dx <= 0) or np.all(dx >= 0)

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