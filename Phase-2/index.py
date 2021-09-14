import xml.etree.ElementTree as etree
import time
import os
import re
import json
import Stemmer
import pickle as pkl
import sys
from itertools import product
from string import ascii_lowercase


PATH_WIKI_XML = sys.argv[1]
PATH_INDEX = sys.argv[2]

start_time = time.time()

total_characters = ascii_lowercase+"0123456789"

indexFilesList = [''.join(i) for i in product(total_characters, repeat = 2)]
empty_dic = {}
for i in indexFilesList:
    file_path = os.path.join(PATH_INDEX, i)
    with open(file_path, "w") as f:
        f.write(json.dumps(empty_dic, indent=0, separators=(",", ":")))
        f.close()

temp_inverted_index={}
for i in indexFilesList:
    temp_inverted_index[i]={}

temp_title_dict={}
title_doc_count=1

pathWikiXML = PATH_WIKI_XML

totalCount = 0
title = None
count_ns=[]

stemmer = Stemmer.Stemmer('english')

with open('stopwords.pkl', 'rb') as f:
    stopword_set = pkl.load(f)
    f.close()
stopword_set.add('category')

string_garbage = re.compile(r"{{[^{}]*?}}")
links_garbage = re.compile(r"(https?://[^| ]+)")
token_reg = re.compile(r"[a-zA-Z0-9]+")
number_garbage = re.compile(r"[0-9]+[a-z]+[0-9a-z]*")
parse_references = re.compile(r"(\*?{{.*\|)(title=.*?)(\|.*?}})")
parse_ext_links = re.compile(r"( *\* *\[[^ ]*)(.*?)(\])")
parse_infobox=re.compile(r"{{infobox((.|\n)*)}}\n")
# parse_infobox = re.compile(r"({{infobox.*)(\|.*)(\|.*?}}\n)")
parse_categories =re.compile(r"\[\[category:[^\n ]*?\]\]")

def hms_string(sec_elapsed):
    h = int(sec_elapsed / (60 * 60))
    m = int((sec_elapsed % (60 * 60)) / 60)
    s = sec_elapsed % 60
    return "{}:{:>02}:{:>05.2f}".format(h, m, s)


def strip_tag_name(t):
    t = elem.tag
    idx = k = t.rfind("}")
    if idx != -1:
        t = t[idx + 1:]
    return t


def addTempIndex2Files(temp_inverted_index):
    for i in indexFilesList:
        file_path = os.path.join(PATH_INDEX, i)
        addInvertedIndex=temp_inverted_index[i]
        if addInvertedIndex:            
            with open(file_path, 'r') as f:
                inverted_index = json.load(f)
                f.close()
            
            for token in addInvertedIndex.keys():
                if token not in inverted_index:
                    inverted_index[token] = {}
                    
                for field in addInvertedIndex[token].keys():
                    if field not in inverted_index[token]:
                        inverted_index[token][field]={}
                    inverted_index[token][field].update(addInvertedIndex[token][field])
        
            with open(file_path, 'w') as f:
                f.write(json.dumps(inverted_index, indent=0, separators=(",", ":")).replace("\n", ""))
                f.close()
        else:
            continue


def removeNumbers(listOfWords):
    returnList=[]
    for i in listOfWords:
        if len(i)>4 and i[0] in "0123456789":
            continue
        else:
            returnList.append(i)
    return returnList
            
def addCount2Index(word, totalCount,field, freq):
    global temp_inverted_index
    if len(word)>=2:
        key_word = word[0:2]
    elif len(word)<2:
        key_word = word[0]*2
    
    if word not in temp_inverted_index[key_word].keys():
        temp_inverted_index[key_word][word]={field:{totalCount:1}}
    elif word in temp_inverted_index[key_word].keys() and field not in temp_inverted_index[key_word][word].keys():
        temp_inverted_index[key_word][word][field] = {totalCount:1}
    elif word in temp_inverted_index[key_word].keys() and totalCount not in temp_inverted_index[key_word][word][field].keys():
        temp_inverted_index[key_word][word][field][totalCount]=1
    else:
        temp_inverted_index[key_word][word][field][totalCount]+=1
    

def fineTuneRegex(listOfstrings):
    returnListOfStrings=["" for i in range(len(listOfstrings))]
    for i in range(len(listOfstrings)):
        if listOfstrings[i][0]=="{":
            bracket="{"
            inBracket="}"
        else:
            bracket="["
            inBracket="]"
        stack=0
        for j in range(len(listOfstrings[i])):
            if listOfstrings[i][j]==bracket and listOfstrings[i][j+1]==bracket:
                j+=1
                stack+=1
            if listOfstrings[i][j]==inBracket and listOfstrings[i][j+1]==inBracket:
                j+=1
                stack-=1
                if stack ==0:
                    returnListOfStrings[i]=listOfstrings[i][:j+1]
                    break
    while "" in returnListOfStrings:
        returnListOfStrings.remove("")
    return returnListOfStrings
#-----------------------------------------------------FREQ variable
freq = 500
for event, elem in etree.iterparse(pathWikiXML, events=('start', 'end')):
    tname = strip_tag_name(elem.tag)

    if event == 'start':
        if tname == 'page':
            title = ''
            id = -1
            redirect = ''
            text=''
            inrevision = False
            ns = 0
        elif tname == 'revision':
            # Do not pick up on revision id's
            inrevision = True
    else:
        if tname == 'title':
            title = elem.text
            totalCount += 1

            if not title:
                continue
            title_1 = title.lower()
            temp_title_1=re.findall(token_reg, title_1)
            temp_title=[i for i in temp_title_1 if i not in stopword_set]
            temp_title = stemmer.stemWords(temp_title)
#------------------------------- Adding Title tokens to the index
            for i in temp_title:
                if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                    stemmed_i = i
                    addCount2Index(stemmed_i, totalCount, 't', freq)

        elif tname == 'id' and not inrevision:
            id = int(elem.text)
        elif tname == 'ns':
            ns = int(elem.text)
        elif tname == 'text':
            text = elem.text
            if not text:
                continue
            text_1 = text.lower()
            complete_text = text_1

            text_split=text_1.split("\n")
            for i in range(len(text_split)):
                if len(text_split[i])>2:
                    if text_split[i][0:3]=="# 2": #or text_split[i][0]=='&':
                        text_split[i]=""
            text="\n".join(text_split)
            text_1 = re.sub(string_garbage, '', text)
            text_1 = re.sub(parse_infobox, '', text_1)
            text_1 = re.sub(parse_categories, '', text_1)
            text_1 = re.sub(parse_references, '', text_1)
            text_1 = re.sub(parse_ext_links, '', text_1)
            text_1 = re.sub(links_garbage, '', text_1)
            text = re.sub(number_garbage, '', text_1)
            text_1 = re.findall(token_reg, text)
            text = [i for i in text_1 if i not in stopword_set]
            
            text = removeNumbers(text)
            temp_text = stemmer.stemWords(text)
#---------------------------- Adding body tokens to inverted index
            for i in temp_text:
                if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                    stemmed_i = i
                    addCount2Index(stemmed_i, totalCount, 'b', freq)
            
            text_2 = complete_text

            
            temp_cat_reg = re.findall(parse_categories, text_2)
            if len(temp_cat_reg)>0:
                text_2 = " ".join(temp_cat_reg)
                text_2 = re.sub(links_garbage, '', text_2)

                text_2 = re.sub(number_garbage, '', text_2)

                text_2_cat = re.findall(token_reg, text_2)
                text_2 = [i for i in text_2_cat if i not in stopword_set]
                text_2 = removeNumbers(text_2)
                
                temp_cat_text = stemmer.stemWords(text_2)
#-------------------------Adding Category tokens to the inverted index
                for i in temp_cat_text:
                    if len(i)<20  and len(i)!=0:
                        stemmed_i = i
                        addCount2Index(stemmed_i, totalCount, 'c', freq)

            text_3 = complete_text
            text_3_info = re.findall(parse_infobox, text_3)
            if len(text_3_info)>0:
                text_3 = [" ".join(i) for i in text_3_info]
                text_3 = " ".join(fineTuneRegex(text_3))
                text_3 = re.sub(links_garbage, '', text_3)

                text_3 = re.sub(number_garbage, '', text_3)
                text_3_info = re.findall(token_reg, text_3)

                text_3 = [i for i in text_3_info if i not in stopword_set]
                text_3 = removeNumbers(text_3)
                
                temp_info_text = stemmer.stemWords(text_3)
#---------------------------- Adding infobox tokens to the inverted index            
                for i in temp_info_text:
                    if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                        stemmed_i = i
                        addCount2Index(stemmed_i, totalCount, 'i', freq)
                
            text_4 = complete_text
            if len(re.findall(r"==references==", text_4))>0 and len(re.findall(r"==external links==", text_4))>0:
                text_4_ref = text_4.split("==references==")[1]
                text_5_extlin = text_4.split("==external links==")[1]
                text_4 = text_4_ref.replace(text_5_extlin, "")
                temp_ref_reg=re.findall(parse_references, text_4)
                if len(temp_ref_reg)>0:
                    text_4_ref=[i[1] for i in temp_ref_reg]

                    text_4 = " ".join(text_4_ref)
                    text_4 = re.sub(links_garbage, '', text_4)

                    text_4 = re.sub(number_garbage, '', text_4)
                    text_4_ref = re.findall(token_reg, text_4)

                    text_4 = [i for i in text_4_ref if i not in stopword_set]

                    text_4 = removeNumbers(text_4)

                    temp_ref_text = stemmer.stemWords(text_4)
#------------------------ Adding reference tokens to the inverted index
                    for i in temp_ref_text:
                        if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                            stemmed_i = i
                            addCount2Index(stemmed_i, totalCount, 'r', freq)

                temp_ext_reg=re.findall(parse_ext_links, text_5_extlin)
                if len(temp_ext_reg)>0:
                    text_5 = [i[1] for i in temp_ext_reg]
                    text_5_extlin = " ".join(text_5)
                    text_5_extlin = re.sub(links_garbage, '', text_5_extlin)
                    text_5_extlin = re.sub(number_garbage, '', text_5_extlin)
                    text_5 = re.findall(token_reg, text_5_extlin)
                    text_5_extlin = [i for i in text_5 if i not in stopword_set]
                    text_5_extlin = removeNumbers(text_5_extlin)
                    
                    temp_extlin_text = stemmer.stemWords(text_5_extlin)
#--------------------------- Adding external link tokens to the inverted index
                    for i in temp_extlin_text:
                        if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                            stemmed_i = i
                            addCount2Index(stemmed_i, totalCount, 'l', freq)
            
            elif len(re.findall(r"==references==", text_4))>0:
                text_4_ref = text_4.split("==references==")[1]
                parse_references = r"(\*?{{.*\|)(title=.*?)(\|.*?}})"
                temp_ref_reg=re.findall(parse_references, text_4_ref)
                if len(temp_ref_reg)>0:
                    text_4_ref=[i[1] for i in temp_ref_reg]

                    text_4 = " ".join(text_4_ref)
                    text_4 = re.sub(links_garbage, '', text_4)

                    text_4 = re.sub(number_garbage, '', text_4)
                    text_4_ref = re.findall(token_reg, text_4)

                    text_4 = [i for i in text_4_ref if i not in stopword_set]
                    text_4 = removeNumbers(text_4)

                    temp_ref_text = stemmer.stemWords(text_4)
#------------------------ Adding reference tokens to the inverted index
                    for i in temp_ref_text:
                        if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                            stemmed_i = i
                            addCount2Index(stemmed_i, totalCount, 'r', freq)
            elif len(re.findall(r"==external links==", text_4))>0:
                text_5_extlin = text_4.split("==external links==")[1]
                temp_ext_reg=re.findall(parse_ext_links, text_5_extlin)
                if len(temp_ext_reg)>0:
                    text_5 = [i[1] for i in temp_ext_reg]
                    text_5_extlin = " ".join(text_5)
                    text_5_extlin = re.sub(links_garbage, '', text_5_extlin)
                    text_5_extlin = re.sub(number_garbage, '', text_5_extlin)
                    text_5 = re.findall(token_reg, text_5_extlin)
                    text_5_extlin = [i for i in text_5 if i not in stopword_set]
                    text_5_extlin = removeNumbers(text_5_extlin)
                    
                    temp_extlin_text = stemmer.stemWords(text_5_extlin)
#--------------------------- Adding external link tokens to the inverted index
                    for i in temp_extlin_text:
                        if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                            stemmed_i = i
                            addCount2Index(stemmed_i, totalCount, 'l', freq)

        elif tname == 'page':
            count_ns.append(ns)
            orig_text=text
                        
            if totalCount%freq==0:
                addTempIndex2Files(temp_inverted_index)
                temp_inverted_index={}
                for i in indexFilesList:
                    temp_inverted_index[i]={}
                print(totalCount)               
        
        elem.clear()

addTempIndex2Files(temp_inverted_index)
temp_inverted_index={}
for i in indexFilesList:
    temp_inverted_index[i]={}

total_keys = 0
for i in indexFilesList:
    file_path = os.path.join(PATH_INDEX, i)
    with open(file_path, "r") as f:
        inverted_index = json.load(f)
        f.close()
    total_keys += len(inverted_index.keys())

print(total_keys)


elapsed_time = time.time() - start_time
print("Total pages: {:,}".format(totalCount))
print("Elapsed time: {}".format(hms_string(elapsed_time)))