import json
import sys

file_name = sys.argv[1]
with open(file_name, "r") as f:
    index=json.load(f)
    f.close()

list_of_keys = str(index.keys()).replace(",", "\n")

with open("temp", "w") as f:
    f.write(list_of_keys)
    f.close()
