import numpy as np


def find_nearest_idx(array, value):
    """
    Finds nearest index in array from value provided

    Params:


    Returns:
        index

    Raises:
        None

    """

    array = np.asarray(array)
    if array.ndim == 1:
        idx = (np.abs(array - value)).argmin()
    else:
        idx = np.sum((np.abs(array - value)), axis=-1).argmin()
    return int(idx)