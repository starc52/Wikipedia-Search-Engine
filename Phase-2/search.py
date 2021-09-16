import time
import os
import re
import json
import Stemmer
import pickle as pkl
import sys
import heapq
from itertools import product
from string import ascii_lowercase
total_characters = ascii_lowercase+"0123456789"

find_lst = []
stemmer = Stemmer.Stemmer('english')
indexFilesList = [''.join(i) for i in product(total_characters, repeat = 2)]

with open('stopwords.pkl', 'rb') as f:
    stopword_set = pkl.load(f)
    f.close()
field_string = "tbicrl"
PATH_INDEX = sys.argv[1]

find_tag = []

prompt = sys.argv[2]

def parseQuery(prompt):
    words={}
    spaceSplit=prompt.split(" ")
    spaceSplitLen=len(prompt.split(" "))
    if spaceSplitLen == 1:
        colonSplit = spaceSplit[0].split(":")
        colonSplitLen = len(spaceSplit[0].split(":"))
        if colonSplitLen ==1:
            fields = [i for i in field_string]
            tokens = stemmer.stemWords(colonSplit)
            words={token:fields for token in tokens}
        elif colonSplitLen >1 and colonSplit[0] in field_string:
            fields = colonSplit[0]
            tokens = stemmer.stemWords([colonSplit[1]])
            words={token:fields for token in tokens}
    else:
        colonSplit = prompt.split(":")
        colonSplitLen = len(colonSplit)
        if colonSplitLen==1:
            fields=[i for i in field_string]
            tokens = [i for i in spaceSplit if i not in stopword_set]
            tokens = stemmer.stemWords(tokens)
            words = {token:fields for token in tokens}
        else:
            colonAfterSpace = [i.split(":") for i in spaceSplit]
            words={}
            for idx, i in enumerate(colonAfterSpace):
                if len(i)>1:
                    endId=0
                    for j in range(idx+1, len(colonAfterSpace)):
                        if len(colonAfterSpace[j])>1:
                            endId=j
                            break
                    if endId==0:
                        endId=len(colonAfterSpace)
                    fields = [i[0]]
                    tokens = [i[1]]
                    for j in range(idx+1, endId):
                        tokens.append(colonAfterSpace[j][0])
                    tokens = [i for i in tokens if i not in stopword_set]
                    tokens = stemmer.stemWords(tokens)
                    words.update({token:fields for token in tokens})
                else:
                    continue
    return words
                    
                    
parsedQuery=parseQuery(prompt)
relevantDocs = []
notFound=0
for key, val in parsedQuery.items():
    result = {}
    if len(key)>=2:
        file_path = os.path.join(PATH_INDEX, key[0:2])
    else:
        file_path = os.path.join(PATH_INDEX, key[0]*2)
    with open(file_path, 'r') as f:
        inverted_index = json.load(f)
        f.close()
    
    if key in inverted_index.keys():
        notFoundCounter=0
        for i in val:
            if i in inverted_index[key].keys():
                result.update(inverted_index[key][i])
            else:
                notFoundCounter+=1
        if notFoundCounter == len(val):
            for i in field_string:
                if i in inverted_index[key].keys():
                    result.update(inverted_index[key][i])
    else:
        notFound+=1
    relevantDocs.append(result)
if notFound == len(parsedQuery.keys()):
    print("Documents not found")



