import time
import os
import re
import json
import Stemmer
import pickle as pkl
import sys
import heapq
import math
from itertools import product
from string import ascii_lowercase
start_time = time.time()
total_characters = ascii_lowercase+"0123456789"

find_lst = []
stemmer = Stemmer.Stemmer('english')
indexFilesList = [''.join(i) for i in product(total_characters, repeat = 2)]

with open('stopwords.pkl', 'rb') as f:
    stopword_set = pkl.load(f)
    f.close()
field_string = "tbicrl"
PATH_INDEX = sys.argv[1]

def hms_string(sec_elapsed):
    h = int(sec_elapsed / (60 * 60))
    m = int((sec_elapsed % (60 * 60)) / 60)
    s = sec_elapsed % 60
    return "{}:{:>02}:{:>05.2f}".format(h, m, s)

with open('progress_file.txt', 'r') as f:
    numberOfPages = int(f.readline())
    f.close()

find_tag = []

prompt = (sys.argv[2]).lower()

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
                    
def loadDocs(prompt):                 
    parsedQuery=parseQuery(prompt)
    relevantDocs = []
    notFound=0
    documentUnion={}
    weightsOfFields={"t":100, "b":15, "c":20, "i":30, "l":10, "r":15}
    with open(os.path.join(PATH_INDEX, "broken"), "rb") as f:
        brokenIndices=pkl.load(f)
        f.close()
    with open(os.path.join(PATH_INDEX, "lastWord"), "rb") as f:
        lastWords=pkl.load(f)
        f.close()
    for key, val in parsedQuery.items():
        result = {}
        if len(key)>=3:
            searchPattern=key[0:3]
        elif len(key)==2:
            searchPattern=key[0:2]+key[0]
        else:
            searchPattern=key[0]*3
        broken=False
        for id, pattern in enumerate(brokenIndices):
            if searchPattern == pattern[0]:
                if id>0:
                    searchRadius=(brokenIndices[id-1][1], brokenIndices[id][1])
                else:
                    searchRadius=(0, brokenIndices[id][1])
                broken=True
                break
        if broken == True:
            for check in range(searchRadius[0], searchRadius[1]):
                if lastWords[check][1]>key:
                    file_name=lastWords[check][0]
                    break
                else:
                    continue
            file_path = os.path.join(PATH_INDEX, file_name)
        else:
            file_path = os.path.join(PATH_INDEX, searchPattern)

        with open(file_path, 'r') as f:
            inverted_index = json.load(f)
            f.close()
        
        if key in inverted_index.keys():
            notFoundCounter=0
            for i in val:
                if i in inverted_index[key].keys():
                    result.update({i:inverted_index[key][i]})
                    idf = math.log(numberOfPages/len(inverted_index[key][i]))
                    for docID in inverted_index[key][i]:
                        if docID not in documentUnion.keys():
                            documentUnion[docID]=1
                        documentUnion[docID]*=math.log(1+(inverted_index[key][i][docID]))*idf*weightsOfFields[i]
                else:
                    notFoundCounter+=1
            if notFoundCounter == len(val):
                for i in inverted_index[key].keys():
                    result.update({i:inverted_index[key][i]})
                    idf = math.log(numberOfPages/len(inverted_index[key][i]))
                    for docID in inverted_index[key][i]:
                        if docID not in documentUnion.keys():
                            documentUnion[docID]=1
                        documentUnion[docID]*=math.log(1+(inverted_index[key][i][docID]))*idf*weightsOfFields[i]
        else:
            notFound+=1
        relevantDocs.append(result)
    if notFound == len(parsedQuery.keys()):
        print("Documents not found")

    for docID in documentUnion.keys():
        count=0
        for wordResult in relevantDocs:
            countIncreased=False
            for fields in wordResult.keys():
                if docID in wordResult[fields].keys():
                    if countIncreased==False:
                        count+=1
                        countIncreased=True
        documentUnion[docID] = documentUnion[docID]*(count**2)
    return documentUnion

def ranking(documentUnion):
    ranked = [(documentUnion[docID], docID) for docID in documentUnion]
    listOfFinal=[]
    ranked_heap=heapq._heapify_max(ranked)
    for i in range(10):
        if len(ranked)!=0:
            listOfFinal.append(heapq._heappop_max(ranked))
        
    return listOfFinal
def printDocs(listOfFinal, factor=50000):
    uniq_dumps = [(int((int(i[1])-1)//factor)+1, i[1]) for i in listOfFinal]
    uniq_dumps.sort(key=lambda x:x[0])
    print_dict={}
    old_file=""
    for i in uniq_dumps:
        file_name = str(i[0])
        if old_file!=file_name:
            with open(os.path.join(PATH_INDEX, file_name+".json"), 'r') as f:
                titleDump=json.load(f)
                f.close()
            print_dict[i[1]]=titleDump[i[1]]
        else:
            print_dict[i[1]]=titleDump[i[1]]
        old_file=file_name
    for i in listOfFinal:
        print(i[1], print_dict[i[1]])

documentUnion=loadDocs(prompt)
listOfFinal=ranking(documentUnion)
printDocs(listOfFinal)
elapsed_time = time.time() - start_time
print("Elapsed time: {}".format(hms_string(elapsed_time)))
