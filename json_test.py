import json

json_file = "Specimens/recipients_conj.json"

with open(json_file) as file:
        data = json.loads(file.read())

print(data)