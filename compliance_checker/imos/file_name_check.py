#!/usr/bin/env python
'''
Compliance Test Suite for testing the netcdf file name
http://www.imos.org.au/
'''

import os.path

from compliance_checker.base import BaseCheck, BaseNCCheck, Result

class IMOSFileNameCheck(BaseNCCheck):

    @classmethod
    def beliefs(cls):
        return {}

    def setup(self, ds):
        head, tail = os.path.split(ds.ds_loc)
        file_names = [ name for name in tail.split('.') ]
        
        file_names_length = len(file_names)
        
        if file_names_length == 0:
            self._file_name = ''
            self._file_extension_name = ''        
        elif file_names_length == 1:
            self._file_name = file_names[0]
            self._file_extension_name = ''
        else: 
            self._file_name = '.'.join([file_names[i] for i in xrange(-1, -(file_names_length+1), -1) if not i == -1])
            self._file_extension_name = file_names[-1]

