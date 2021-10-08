import time
import os
import re
import json
import Stemmer
import pickle as pkl
import sys
import heapq
import math
import multiprocessing
import traceback
from multiprocessing import Pool
from itertools import product, repeat
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

def hms_string(sec_elapsed):
    h = int(sec_elapsed / (60 * 60))
    m = int((sec_elapsed % (60 * 60)) / 60)
    s = sec_elapsed % 60
    return "{}:{:>02}:{:>05.2f}".format(h, m, s)

numberOfPages=31452341

find_tag = []

PATH_QUERY = sys.argv[2]

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
        elif colonSplitLen>1 and len(colonSplit[0])!=1:
            colonAfterSpace = [i.split(":") for i in spaceSplit]
            words={}
            colonsHit=False
            for idx, i in enumerate(colonAfterSpace):
                if len(i)>1:
                    colonsHit=True
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
                    temp_dict={token:fields for token in tokens}
                    for token in temp_dict:
                        if token in words:
                            words[token]+=temp_dict[token]
                        else:
                            words[token]=temp_dict[token]
                    
                elif len(i)==1 and colonsHit==False:
                    tokens = [i[0]]
                    tokens = [i for i in tokens if i not in stopword_set]
                    tokens = stemmer.stemWords(tokens)
                    fields = [i for i in field_string]
                    temp_dict={token:fields for token in tokens}
                    for token in temp_dict:
                        if token in words:
                            words[token]+=temp_dict[token]
                        else:
                            words[token]=temp_dict[token]
                else:
                    continue
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
                    temp_dict={token:fields for token in tokens}
                    for token in temp_dict:
                        if token in words:
                            words[token]+=temp_dict[token]
                        else:
                            words[token]=temp_dict[token]
                else:
                    continue
    return words
prevFilePath=""
def searchWordInIndex(word, parsedQuery, notFound, weightsOfFields, countWordDoc, documentUnion):
    global prevFilePath
    with open(os.path.join(PATH_INDEX, "broken"), "rb") as f:
        brokenIndices=pkl.load(f)
        f.close()
    with open(os.path.join(PATH_INDEX, "lastWord"), "rb") as f:
        lastWords=pkl.load(f)
        f.close()
    if len(word)>=3:
        searchPattern=word[0:3]
    elif len(word)==2:
        searchPattern=word[0:2]+word[0]
    else:
        searchPattern=word[0]*3
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
            if lastWords[check][1]>word:
                file_name=lastWords[check][0]
                break
            else:
                continue
        file_path = os.path.join(PATH_INDEX, file_name)
    else:
        file_path = os.path.join(PATH_INDEX, searchPattern)
    if file_path!=prevFilePath:
        with open(file_path, 'r') as f:
            inverted_index = json.load(f)
            f.close()
    prevFilePath = file_path
    if word in inverted_index.keys():
        for i in parsedQuery[word]:
            if i in inverted_index[word].keys():
                idf = math.log(numberOfPages/len(inverted_index[word][i]))
                for docID in inverted_index[word][i]:
                    if docID not in documentUnion.keys():
                        documentUnion[docID]=0
                    if docID not in countWordDoc.keys():
                        countWordDoc[docID]=1
                    else:
                        countWordDoc[docID]+=1
                    documentUnion[docID]+=math.log(1+(inverted_index[word][i][docID]))*idf*weightsOfFields[i]
    else:
        notFound+=1
    return documentUnion, countWordDoc, notFound                    
def mergeDicts(dict1, dict2):
    if len(dict1)>len(dict2):
        iterDict = dict2.copy()
        otherDict = dict1.copy()
    else:
        iterDict = dict1.copy()
        otherDict = dict2.copy()
    if iterDict:
        for i in iterDict.keys():
            if i in otherDict:
                otherDict[i]+=iterDict[i]
            else:
                otherDict[i]=iterDict[i]
        return otherDict
    else:
        return otherDict

def loadDocs(prompt):                 
    parsedQuery=parseQuery(prompt)
    relevantDocs = []
    notFound=0
    documentUnion={}
    countWordDoc={}
    weightsOfFields={"t":100, "b":75, "c":20, "i":80, "l":10, "r":15}
    
    listOfWords=sorted(parsedQuery.keys())
    if listOfWords[0]=="":
        return {}
    print(listOfWords)
    if len(listOfWords)>6:
        with Pool() as p:
            result=p.starmap(searchWordInIndex, zip(listOfWords, repeat(parsedQuery), repeat(notFound), repeat(weightsOfFields), repeat(countWordDoc), repeat(documentUnion)))
            for wordOut in result:
                try:
                    tempDoc, tempCount, tempNotFound = wordOut
                    notFound+=tempNotFound
                    documentUnion = mergeDicts(tempDoc, documentUnion)
                    countWordDoc = mergeDicts(tempCount, countWordDoc)
                except Exception as exc:
                    print(traceback.format_exc())
                else:
                    pass
    else:
        for key in listOfWords:
            documentUnion, countWordDoc, notFound = searchWordInIndex(key, parsedQuery, notFound, weightsOfFields, countWordDoc, documentUnion)
    if notFound == len(parsedQuery.keys()):
        with open(PATH_QUERY[:-4]+"_op.txt", 'a') as f:
            f.write("Documents not found\n")
            f.close()
        return {}
    for docID in documentUnion.keys():
        documentUnion[docID] = documentUnion[docID]*(countWordDoc[docID]**3)
    return documentUnion

def ranking(documentUnion):
    ranked = [(documentUnion[docID], docID) for docID in documentUnion]
    listOfFinal=[]
    ranked_heap=heapq._heapify_max(ranked)
    for i in range(10):
        if len(ranked)!=0:
            listOfFinal.append(heapq._heappop_max(ranked))
        
    return listOfFinal
def printDocs(listOfFinal, start_time, factor=50000):
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
    with open(PATH_QUERY[:-4]+"_op.txt", 'a') as f:
        for i in listOfFinal:
            f.write(str(i[1])+", "+str(print_dict[i[1]])+"\n")
        elapsed_time = time.time() - start_time
        f.write(str(elapsed_time)+"\n")
        f.write("\n")
        
        f.close()
if __name__ == '__main__':
    with open(PATH_QUERY, 'r') as f:
        queries=f.readlines()
        f.close()

    for i in queries:
        if i:
            start_time = time.time()
            documentUnion=loadDocs(i.replace("\n", "").lower())
            if documentUnion:
                listOfFinal=ranking(documentUnion)
                printDocs(listOfFinal, start_time,  60000)
