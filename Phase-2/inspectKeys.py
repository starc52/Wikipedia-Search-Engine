import json
import sys

file_name = sys.argv[1]
with open(file_name, "r") as f:
    index=json.load(f)
    f.close()
tupleList=[]
for i in index.keys():
    count=0
    for j in index[i]:
        count+=len(index[i][j].keys())
    tupleList.append((i, count))
tupleList.sort(key= lambda x:x[1])
print(tupleList)
