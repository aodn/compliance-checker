#!/usr/bin/env python
'''
Compliance Test Suite for testing the netcdf file name
http://www.imos.org.au/
'''

import sys
import argparse
import os.path
import datetime
import re

import yaml
from pkg_resources import resource_filename

from compliance_checker.base import BaseCheck, BaseNCCheck, Result


# Initial reference tables for file name check up
facility_code_file = resource_filename('compliance_checker', 'imos/facility_code.yml')
stream = file(facility_code_file, 'r')    # 'document.yaml' contains a single YAML document.
facility_code_list = yaml.load(stream)

platform_code_file = resource_filename('compliance_checker', 'imos/platform_code.yml')
stream = file(platform_code_file, 'r')    # 'document.yaml' contains a single YAML document.
platform_code_list = yaml.load(stream)


class IMOSFileNameCheck(BaseNCCheck):

    @classmethod
    def beliefs(cls):
        return {}

    def setup(self, ds):
                
        if hasattr(ds, 'ds_loc'):
            dataset_name = ds.ds_loc
        else:
            parser = argparse.ArgumentParser()
            parser.add_argument('--test', '-t', '--test=', '-t=', action='append')
            parser.add_argument('--criteria', '-c', nargs='?', default='normal')
            parser.add_argument('--verbose' , '-v', action="count")
            parser.add_argument('-f', '--format', default='text')
            parser.add_argument('-o', '--output', default='-', action='store')
            parser.add_argument('dataset_location', nargs='+')

            args = parser.parse_args()
            dataset_name = args.dataset_location[0]

        head, tail = os.path.split(dataset_name)
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

    def check_file_name_field2(self, ds):
        '''
        Check file name field2 and ensure it is valid facility, sub facility code
        '''
        ret_val = []
        result_name = ['file_name','check_file_name_field2']
        reasoning = ["File name field2 is not valid facility, sub facility code'"]

        if self._file_names_length >= 2:
            if self._file_names[1] not in facility_code_list:
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

        if self._file_names_length >= 3:
            if re.search('^[ABCEFGIKMOPRSTUVWZ]+$', self._file_names[2]) == None:
                result = Result(BaseCheck.HIGH, False, result_name, reasoning)
            else:
                result = Result(BaseCheck.HIGH, True, result_name, None)
        else:
            result = Result(BaseCheck.HIGH, False, result_name, reasoning)

        ret_val.append(result)

        return ret_val

    def check_file_name_field4(self, ds):
        '''
        Check file name field4 matches time_coverage_start attribute
        '''
        ret_val = []
        result_name = ['file_name','check_file_name_field4']
        reasoning = ["File name field4 doesn't match time_coverage_start attribute"]

        time_coverage_start = getattr(ds.dataset, 'time_coverage_start', None)
        passed = False
        if time_coverage_start is not None:
            # time_coverage_start format is yyyy-mm-ddTHH:MM:SSZ while
            # field4 format is yyyymmddTHHMMSSZ
            time_coverage_start = time_coverage_start.replace("-", "")
            time_coverage_start = time_coverage_start.replace(":", "")
            if self._file_names_length >= 4:
                field4 = self._file_names[3]
                if field4 != time_coverage_start:
                    passed = False
                else:
                    passed = True

            if passed:
                result = Result(BaseCheck.HIGH, True, result_name, None)
            else:
                result = Result(BaseCheck.HIGH, False, result_name, reasoning)

            ret_val.append(result)

        return ret_val

    def check_file_name_field5(self, ds):
        '''
        Check file name field5 matches platform_code or site_code attribute
        Check file name field5 is valid platform code
        '''
        ret_val = []
        result_name = ['file_name','check_file_name_field5']

        if self._file_names_length >= 5:
            reasoning = ["File name field5 is not valid platform code"]
            if self._file_names[4] not in platform_code_list:
                result = Result(BaseCheck.HIGH, False, result_name, reasoning)
            else:
                result = Result(BaseCheck.HIGH, True, result_name, None)

            ret_val.append(result)

            reasoning = ["File name field5 doesn't match platform_code or site_code attribute"]
            platform_code = getattr(ds.dataset, 'platform_code', None)
            site_code = getattr(ds.dataset, 'site_code', None)
            check_values = []

            check_values.append(platform_code)
            check_values.append(site_code)

            if any(check_values):
                field5 = self._file_names[4]

                if field5 in check_values:
                    result = Result(BaseCheck.HIGH, True, result_name, None)
                else:
                    result = Result(BaseCheck.HIGH, False, result_name, reasoning)

                ret_val.append(result)

        return ret_val


    def check_file_name_field6(self, ds):
        '''
        Check file name field6 is one of FV00, FV01, FV02 and consistent with
        file_version attribute, if it exists
        Field should be 'FV0X' where file_version starts with 'LEVEL X'
        '''
        ret_val = []
        result_name = ['file_name','check_file_name_field6']
        reasoning = ["File name field6 is not one of FV00, FV01, FV02"]
        skip = False
        passed = False
        if self._file_names_length >= 6:
            field6 = self._file_names[5]
            if field6 == 'FV00' or field6 == 'FV01' or field6 == 'FV02':
                passed = True

                file_version = getattr(ds.dataset, 'file_version', None)

                if file_version is not None:
                    passed = False
                    file_version_splits = [split for split in file_version.split(' ')]

                    if len(file_version_splits) >= 2:
                        if field6[3] == file_version_splits[1]:
                            passed = True
                        else:
                            passed = False
                    else:
                        passed = False
                else:
                    skip = True
            else:
                passed = False
        else:
            passed = False

        if not skip:
            if passed:
                result = Result(BaseCheck.HIGH, True, result_name, None)
            else:
                result = Result(BaseCheck.HIGH, False, result_name, reasoning)

        ret_val.append(result)

        return ret_val

    def check_file_name_field7_to_field10(self, ds):
        '''
        Check file name field7 to filed 10 to meet one of the below conditions:
        1) is a non-empty string (product type)
        2) matches time_coverage_end attribute, format "END-YYYYMMDDTHHMMSSZ"
        3) matches date_created attribute, format "C-YYYYMMDDTHHMMSSZ"
        4) matches regexp "PART\d+"
        
        Each condition must only match one field
        '''
        ret_val = []
        result = None
        result_name = ['file_name','check_file_name_field7_to_field10']
        reasoning = ["Some of values from filed 7 to filed 10 are not correct"]
        success = [None, None, None, None]

        for i in range(6, self._file_names_length):
            field = self._file_names[i]

            try:
                if field.startswith('END-'):
                    field_date = field[4:]
                    datetime.datetime.strptime(field_date, '%Y%m%dT%H%M%SZ')

                    if success[0] == None:
                        success[0] = True
                        continue

                if field.startswith('C-'):
                    field_date = field[2:]
                    datetime.datetime.strptime(field_date, '%Y%m%dT%H%M%SZ')

                    if success[1] == None:
                        success[1] = True
                        continue

            except ValueError:
                pass

            pattern = r'^PART\d+'
            if re.search(pattern,  field):
                if success[2] == None:
                    success[2] = True
                    continue

            if isinstance(field, basestring):
                if field and not field.isdigit():
                    if success[3] == None:
                        success[3] = True
                        continue

        if self._file_names_length > 6:
            trues = [suc for suc in success if suc]
            if len(trues) == self._file_names_length-6:
                result = Result(BaseCheck.HIGH, True, result_name, None)
            else:
                result = Result(BaseCheck.HIGH, False, result_name, reasoning)

            ret_val.append(result)

        return ret_val
