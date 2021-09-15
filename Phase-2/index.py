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

string_garbage = re.compile(r"\[\[[^\[\]]*\]\]|{{[^{}]*?}}")
links_garbage = re.compile(r'(https?://\S+)')#re.compile(r"(https?://[^| ]+)")
token_reg = re.compile(r"[a-zA-Z0-9]+")
number_garbage = re.compile(r"[0-9]+[a-z]+[0-9a-z]*")
parse_references = re.compile(r"(\*?{{.*\|)(title=.*?)(\|.*?}})")
parse_ext_links = re.compile(r"( *\* *?\[[^ ]*)(.*?)(\])")
css_reg = re.compile(r"{\|(.*?)\|}", re.DOTALL)
# parse_infobox=re.compile(r"{{infobox *\n}}\n", re.DOTALL)
# parse_infobox = re.compile(r"({{infobox.*)(\|.*)(\|.*?}}\n)")
parse_categories =re.compile(r"\[\[category:.*?\]\]")
remove_comments = re.compile(r"&lt;!--.*?--&gt;", re.DOTALL)
html_tags = re.compile(r"&lt;.*?&gt;")

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

def addTitle2Files(temp_title_dict):
    global title_doc_count
    file_path = os.path.join(PATH_INDEX, str(title_doc_count)+".json")
    with open(file_path, "w") as f:
        f.write(json.dumps(temp_title_dict, indent=0, separators=(",", ":")).replace("\n", ""))
        f.close()
    title_doc_count+=1

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
            
def addCount2Index(word, totalCount,field):
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
    

def bracketStack(strings):
    returnString=""
    bracket="{"
    inBracket="}"
    stack=1
    for j in range(len(strings)):
        if j+1<len(strings) and strings[j]==bracket and strings[j+1]==bracket:
            j+=1
            stack+=1
        if j+1<len(strings) and strings[j]==inBracket and strings[j+1]==inBracket:
            j+=1
            stack-=1
            if stack ==0:
                returnString=strings[:j+1]
                break
    return returnString

def parseBody(totalCount, textString):
    info_text=""
    reference_text = ""
    external_link_text ="" 
    categories_text=[]
    if len(re.findall(r"{{infobox", textString))>0:
        infoBoxContent=textString.split("{{infobox")[1]
        info_text=bracketStack(infoBoxContent)
        textString.replace(info_text, "")
    
    categories_text = re.findall(parse_categories, textString)
    for i in categories_text:
        textString.replace(i, "")
    if len(re.findall(r"==references==", textString))>0 and len(re.findall(r"==external links==", textString))>0:
        textStringRef = textString.split("==references==")[1]
        external_link_text = textString.split("==external links==")[1]
        reference_text = textStringRef.replace(external_link_text, "")
        textString = textString.replace(reference_text, "")
        textString = textString.replace(external_link_text, "")
    elif len(re.findall(r"==references==", textString))>0:
        reference_text = textString.split("==references==")[1]
        textString = textString.replace(reference_text, "")
    elif len(re.findall(r"==external links==", textString))>0:
        external_link_text = textString.split("==external links==")[1]
        textString = textString.replace(external_link_text, "")
    ## Body
    text_split=textString.split("\n")
    for i in range(len(text_split)):
        if len(text_split[i])>2:
            if text_split[i][0:3]=="# 2":
                text_split[i]=""
    textString="\n".join(text_split)
    textString = re.sub(string_garbage, '', textString)    
    textString = re.sub(number_garbage, '', textString)
    textTokens = re.findall(token_reg, textString)
    stopTextTokens = [i for i in textTokens if i not in stopword_set]
    
    stopTextTokens = removeNumbers(stopTextTokens)
    stemTextTokens = stemmer.stemWords(stopTextTokens)
    for i in stemTextTokens:
        if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
            addCount2Index(i, totalCount, 'b')
    ## Infobox
    if len(info_text)>0:
        info_text = re.sub(links_garbage, '', info_text)
        info_text = re.sub(number_garbage, '', info_text)
        infoTokens = re.findall(token_reg, info_text)
        stopInfoTokens = [i for i in infoTokens if i not in stopword_set]
        stopInfoTokens = removeNumbers(stopInfoTokens)
        
        stemInfoTokens = stemmer.stemWords(stopInfoTokens)
        for i in stemInfoTokens:
            if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                addCount2Index(i, totalCount, 'i')
    ## Categories
    if len(categories_text)>0:
        categories_text = " ".join(categories_text)
        catTokens = re.findall(token_reg, categories_text)
        stopCatTokens = [i for i in catTokens if i not in stopword_set]
        stopCatTokens = removeNumbers(stopCatTokens)
        
        stemCatTokens = stemmer.stemWords(stopCatTokens)
        for i in stemCatTokens:
            if len(i)<20  and len(i)!=0:
                addCount2Index(i, totalCount, 'c')
    ## References
    if len(reference_text)>0:
        reference_text=re.findall(parse_references, reference_text)
        if len(reference_text)>0:
            refExtText=[i[1] for i in reference_text]
            refExtText = " ".join(refExtText)
            linkRef = re.sub(links_garbage, '', refExtText)
            numRef = re.sub(number_garbage, '', linkRef)
            refTokens = re.findall(token_reg, numRef)
            stopRefTokens = [i for i in refTokens if i not in stopword_set]
            stopRefTokens = removeNumbers(stopRefTokens)
            stemRefTokens = stemmer.stemWords(stopRefTokens)
            for i in stemRefTokens:
                if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0 and i!="reflist":
                    addCount2Index(i, totalCount, 'r')    
    ## External Links
    if len(external_link_text)>0:
        extLinkText=re.findall(parse_ext_links, external_link_text)
        if len(extLinkText)>0:
            extLinkList = [i[1] for i in extLinkText]
            extLinkString = " ".join(extLinkList)
            extLinkString = re.sub(links_garbage, '', extLinkString)
            extLinkString = re.sub(number_garbage, '', extLinkString)
            extLinkTokens = re.findall(token_reg, extLinkString)
            stopExtLink = [i for i in extLinkTokens if i not in stopword_set]
            stopExtLink = removeNumbers(stopExtLink)
            stemExtLink = stemmer.stemWords(stopExtLink)
            for i in stemExtLink:
                if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                    addCount2Index(i, totalCount, 'l')
#-----------------------------------------------------FREQ variable
freqD = 500000
freqT=100000
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
            totalCount += 1
        elif tname == 'revision':
            # Do not pick up on revision id's
            inrevision = True
    else:
        if tname == 'title':
            title = elem.text

            if not title:
                continue
            temp_title_dict.update({totalCount:title})
            title_1 = title.lower()
            temp_title_1=re.findall(token_reg, title_1)
            temp_title=[i for i in temp_title_1 if i not in stopword_set]
            temp_title = stemmer.stemWords(temp_title)
#------------------------------- Adding Title tokens to the index
            for i in temp_title:
                if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                    stemmed_i = i
                    addCount2Index(stemmed_i, totalCount, 't')

        elif tname == 'id' and not inrevision:
            id = int(elem.text)
        elif tname == 'ns':
            ns = int(elem.text)
        elif tname == 'text':
            text = elem.text
            if not text:
                continue
            text_1 = text.lower()
            text_1 = re.sub(html_tags, '', text_1)
            complete_text = text_1
            parseBody(totalCount, complete_text)

        elif tname == 'page':
            count_ns.append(ns)
            orig_text=text
            if totalCount%freqT==0:
                addTitle2Files(temp_title_dict)
                temp_title_dict={}
            if totalCount%freqD==0:
                addTempIndex2Files(temp_inverted_index)
                temp_inverted_index={}
                for i in indexFilesList:
                    temp_inverted_index[i]={}
            if totalCount%1000==0:
                print(totalCount)        
        elem.clear()

addTempIndex2Files(temp_inverted_index)
temp_inverted_index={}
for i in indexFilesList:
    temp_inverted_index[i]={}
addTitle2Files(temp_title_dict)
temp_title_dict={}

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