# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

# Miscellaneous utility code

import contextlib
import functools
import pathlib
import socket
import warnings


def implements(f):
    def decorator(g):
        g.__doc__ = f.__doc__
        return g
    return decorator


def _deprecate_api(old_name, new_name, api, next_version):
    msg = ('pyarrow.{} is deprecated as of {}, please use pyarrow.{} instead'
           .format(old_name, next_version, new_name))

    def wrapper(*args, **kwargs):
        warnings.warn(msg, FutureWarning)
        return api(*args, **kwargs)
    return wrapper


def _is_path_like(path):
    # PEP519 filesystem path protocol is available from python 3.6, so pathlib
    # doesn't implement __fspath__ for earlier versions
    return (isinstance(path, str) or
            hasattr(path, '__fspath__') or
            isinstance(path, pathlib.Path))


def _stringify_path(path):
    """
    Convert *path* to a string or unicode path if possible.
    """
    if isinstance(path, str):
        return path

    # checking whether path implements the filesystem protocol
    try:
        return path.__fspath__()  # new in python 3.6
    except AttributeError:
        # fallback pathlib ckeck for earlier python versions than 3.6
        if isinstance(path, pathlib.Path):
            return str(path)

    raise TypeError("not a path-like object")


def product(seq):
    """
    Return a product of sequence items.
    """
    return functools.reduce(lambda a, b: a*b, seq, 1)


def get_contiguous_span(shape, strides, itemsize):
    """
    Return a contiguous span of N-D array data.

    Parameters
    ----------
    shape : tuple
    strides : tuple
    itemsize : int
      Specify array shape data

    Returns
    -------
    start, end : int
      The span end points.
    """
    if not strides:
        start = 0
        end = itemsize * product(shape)
    else:
        start = 0
        end = itemsize
        for i, dim in enumerate(shape):
            if dim == 0:
                start = end = 0
                break
            stride = strides[i]
            if stride > 0:
                end += stride * (dim - 1)
            elif stride < 0:
                start += stride * (dim - 1)
        if end - start != itemsize * product(shape):
            raise ValueError('array data is non-contiguous')
    return start, end


def find_free_port():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    with contextlib.closing(sock) as sock:
        sock.bind(('', 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.getsockname()[1]
