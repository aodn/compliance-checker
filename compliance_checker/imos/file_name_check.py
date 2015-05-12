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

    def check_extension_name(self, ds):
        ret_val = []
        result_name = ['file_name','check_extension_name']
        reasoning = ["File extension name is not equal to nc"]

        if not self._file_extension_name == 'nc':
            result = Result(BaseCheck.HIGH, False, result_name, reasoning)
        else:
            result = Result(BaseCheck.HIGH, True, result_name, None)

        ret_val.append(result)

        return ret_val

    def check_file_name(self, ds):
        ret_val = []
        result_name = ['file_name','check_file_name']
        reasoning = ["File name doesn't contain 6 to 10 fields, separated by '_'"]

        file_names = [ name for name in self._file_name.split('_') ]

        if len(file_names) >= 6 and len(file_names) <= 10:
            result = Result(BaseCheck.HIGH, True, result_name, None)
        else:
            result = Result(BaseCheck.HIGH, False, result_name, reasoning)

        ret_val.append(result)

        return ret_val
