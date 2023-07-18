#!/usr/bin/env python3
import os
import requests
import json

feedback_files = os.listdir('/data/feedback')

for file in feedback_files:
        file_path = '/data/feedback/' + file
        with open(file_path) as feedback_file:
                content = feedback_file.readlines()
        feedback_dict = {'title': content[0][:-1], 'name': content[1][:-1], 'date': content[2][:-1], 'feedback': content[3]}
        feedback = json.dumps(feedback_dict)
        response = requests.post('http://34.68.105.41/feedback', json=feedback)
        print(response.status_code)
