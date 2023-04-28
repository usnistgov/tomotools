# -*- coding: utf-8 -*-
#
# This file is part of TomoTools

"""
Utility module for TomoTools package.

@author: Andrew Herzing
"""

import numpy as np
from tomotools.io import numpy_to_tomo_stack
from tomotools.base import TomoStack


def register_serialem_stack(stack, method='ECC'):
    """
    Register a multi-frame series collected by SerialEM.

    Parameters
    ----------
    stack : Hyperspy Signal2D
        Signal of shape [ntilts, nframes, ny, nx].

    method : string
        Stack registration method to use.

    Returns
    ----------
    reg : TomoStack object
        Result of aligning and averaging frames at each tilt with shape [ntilts, ny, nx]

    """

    reg = np.zeros([stack.data.shape[0], stack.data.shape[2],
                   stack.data.shape[3]], stack.data.dtype)
    for i in range(0, stack.data.shape[0]):
        temp = TomoStack(np.float32(stack.data[i]))
        reg[i, :, :] = temp.stack_register(method=method).data.mean(0)
    reg = numpy_to_tomo_stack(reg)
    return reg
