#!/usr/bin/env python3

import re
import csv

file_location = input("Enter CSV file location (Use \ in Wondows and / in MacOS or Linux): ")
new_file_location = input("File Location of Report: ")

file_pattern = r".csv$"

def check_location(location, pattern):
	result = re.search(pattern, location)
	return result

def read_employees(csv_file_location):
        csv.register_dialect('empDialect', skipinitialspace=True, strict=True)
        employee_file = csv.DictReader(open(csv_file_location), dialect = 'empDialect')
        employee_list = []
        for data in employee_file:
                employee_list.append(data)
        return employee_list



def process_data(employee_list):
        department_list = []
        for employee_data in employee_list:
                department_list.append(employee_data['Clan'])
        department_data = {}
        for department_name in set(department_list):
                department_data[department_name] = department_list.count(department_name)
        return department_data



def write_report(dictionary, report_file):
        with open(report_file, "w+") as f:
                for k in sorted(dictionary):
                        f.write(str(k)+':'+str(dictionary[k])+'\n')
                f.close()

location_check = check_location(file_location, file_pattern)
if location_check != None:
	employee_list = read_employees(file_location)
	dictionary = process_data(employee_list)
	report_location = new_file_location + "report.txt"
	write_report(dictionary, report_location)

