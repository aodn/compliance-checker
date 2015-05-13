#!/usr/bin/env python
'''
Compliance Test Suite for testing the netcdf file name
http://www.imos.org.au/
'''

import os.path
import re

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
        
        self._file_names = [ name for name in self._file_name.split('_') ]
        self._file_names_length = len(self._file_names)

    def check_extension_name(self, ds):
        '''
        Check file extension name and ensure it equals to nc
        '''
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
        '''
        Check file name and ensure it contains 6 to 10 fields, separated by '_'
        '''
        ret_val = []
        result_name = ['file_name','check_file_name']
        reasoning = ["File name doesn't contain 6 to 10 fields, separated by '_'"]

        if self._file_names_length >= 6 and self._file_names_length <= 10:
            result = Result(BaseCheck.HIGH, True, result_name, None)
        else:
            result = Result(BaseCheck.HIGH, False, result_name, reasoning)

        ret_val.append(result)

        return ret_val

    def check_file_name_field1(self, ds):
        '''
        Check file name field1 and ensure it is "IMOS"
        '''
        ret_val = []
        result_name = ['file_name','check_file_name_field1']
        reasoning = ["File name field1 is not 'IMOS'"]


        if self._file_names_length >= 0:
            if self._file_names[0] != 'IMOS':
                result = Result(BaseCheck.HIGH, False, result_name, reasoning)
            else:
                result = Result(BaseCheck.HIGH, True, result_name, None)
        else:
            result = Result(BaseCheck.HIGH, False, result_name, reasoning)

        ret_val.append(result)

        return ret_val

    def check_file_name_field3(self, ds):
        '''
        Check file name field3 and ensure it is made up of the characters "ABCEFGIKMOPRSTUVWZ"
        '''
        ret_val = []
        result_name = ['file_name','check_file_name_field3']
        reasoning = ["File name field3 is not made up of characters 'ABCEFGIKMOPRSTUVWZ'"]

        if self._file_names_length >= 2:
            if re.search('^[ABCEFGIKMOPRSTUVWZ]+$', self._file_names[2]) == None:
                result = Result(BaseCheck.HIGH, False, result_name, reasoning)
            else:
                result = Result(BaseCheck.HIGH, True, result_name, None)
        else:
            result = Result(BaseCheck.HIGH, False, result_name, reasoning)

        ret_val.append(result)

        return ret_val

    def check_file_name_field6(self, ds):
        '''
        Check file name field6 is one of FV00, FV01, FV02 and consistent with
        file_version attribute, if it exists.
        Field should be 'FV0X' where file_version starts with 'LEVEL X'
        ''' 
        ret_val = []
        result_name = ['file_name','check_file_name_field6']
        reasoning = ["File name field6 is not one of FV00, FV01, FV02"]

        file_version = getattr(ds.dataset, 'file_version', None)
        passed = False
        if file_version is not None:
            file_version_splits = [split for split in file_version.split(' ')] 

            if len(file_version_splits) >= 2:
                if self._file_names_length >= 6:
                    field6 = self._file_names[5]
                    if len(field6) != 4:
                        passed = False
                    else:
                        if field6 == 'FV00' or field6 == 'FV01' or field6 == 'FV02':
                            if field6[3] == file_version_splits[1]:
                                passed = True
                            else:
                                passed = False
                        else:
                            passed = False
                else:
                    passed = False

                if passed:
                    result = Result(BaseCheck.HIGH, True, result_name, None)
                else:
                    result = Result(BaseCheck.HIGH, False, result_name, reasoning)

                ret_val.append(result)
        return ret_val
