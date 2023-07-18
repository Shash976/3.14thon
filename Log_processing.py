#!/usr/bin/env python3

import csv
import re
from time import sleep
import operator

per_user = {}
user_message_list = []
error_messages_number = {}
user_entries_info = {}
user_entries_error = {}

with open('syslog.log') as log:
	logs = ""
	for line in log:
		logs = logs + line.strip() + "\n"
log_line = logs.split('\n')
log_line.remove("")

for line in log_line:
	search_result = re.findall(r"ticky: (ERROR|INFO) ([\w ]*).*\(([\w\.]+)\)", line)

	message = search_result[0][0]
	type = search_result[0][1]
	user = search_result[0][2]

	if message.strip() == 'ERROR':
		if type.strip() not in error_messages_number:
			error_messages_number[type.strip()] = 0
		error_messages_number[type.strip()] += 1
		if user.strip() not in user_entries_error:
			user_entries_error[user.strip()] = 0
		user_entries_error[user.strip()] += 1

	elif message.strip() == 'INFO':
		if user.strip() not in user_entries_info:
			user_entries_info[user.strip()] = 0
		user_entries_info[user.strip()] += 1

per_user = {**user_entries_info, **user_entries_error}

for key, value in per_user.items():
	if key in user_entries_info and key in user_entries_error:
		per_user[key] = [value , user_entries_info[key]]

sorted_error_rank = sorted(error_messages_number.items(), key=operator.itemgetter(1), reverse=True)
sorted_per_user = sorted(per_user.items())



with open('error_message.csv', 'w') as error_csv:
	csv_out=csv.writer(error_csv)
	csv_out.writerow(['error', 'occurances'])
	csv_out.writerows(sorted_error_rank)

with open('user_statistics.csv', 'w') as user_csv:
	csv_out=csv.writer(user_csv)
	csv_out.writerow(['user', 'error', 'info'])
	csv_out.writerows(sorted_per_user)

print (sorted_per_user, sorted_error_rank)
