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

indexFilesList = [''.join(i) for i in product(total_characters, repeat = 3)]
empty_dic = {}
for i in indexFilesList:
    file_path = os.path.join(PATH_INDEX, i)
    try:
        os.remove(file_path)
    except:
        print("Tried to remove a non existent file")

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
stopword_set.add('reference')
stopword_set.add('title')
print(len(stopword_set))

string_garbage = re.compile(r"{{[^{}]*?}}")
links_garbage = re.compile(r'(https?://\S+)')#re.compile(r"(https?://[^| ]+)")
token_reg = re.compile(r"[a-zA-Z0-9]+")
number_garbage = re.compile(r"[0-9]+[a-z]+[0-9a-z]*")
parse_references = re.compile(r"(\*?{{.*\|)(title=.*?)(\|.*?}})")
parse_ext_links = re.compile(r"( *\* *?\[[^ ]*)(.*?)(\])")
css_reg = re.compile(r"{\|(.*?)\|}", re.DOTALL)
parse_infobox=re.compile(r"{{infobox *\n}}\n", re.DOTALL)
# parse_infobox = re.compile(r"({{infobox.*)(\|.*)(\|.*?}}\n)")
parse_categories =re.compile(r"\[\[category:.*?\]\]")
# remove_comments = re.compile(r"&lt;!--.*?--&gt;", re.DOTALL)
html_tags = re.compile(r"(&lt;([a-zA-Z0-9]*).*?&gt;).*?\1")
ref_garbage = re.compile(r"&lt;ref(.*?)?&gt;(.*?)&lt;/ref&gt;|<ref(.*?)?>(.*?)</ref>", re.DOTALL)#)

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
            if not os.path.isfile(file_path):
                with open(file_path, "w") as f:
                    f.write(json.dumps({}, indent=0, separators=(",", ":")))
                    f.close()
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
        elif len(i)>2 and i[0] in "3456789":
            continue
        else:
            returnList.append(i)
    return returnList
            
def addCount2Index(word, totalCount,field):
    global temp_inverted_index
    if len(word)>=3:
        key_word = word[0:3]
    elif len(word)==2:
        key_word = word[0:2]+word[0]
    elif len(word)==1:
        key_word = word[0]*3
    
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
countOf2 = 0
countOfText=0
def parseBody(totalCount, textString):
    global countOf2
    info_text=""
    reference_text = []
    external_link_text ="" 
    categories_text=[]

    if len(re.findall(r"{{infobox", textString))>0:
        infoBoxContent=textString.split("{{infobox")[1]
        info_text=bracketStack(infoBoxContent)
        textString.replace(info_text, "")
    reference_text=re.findall(ref_garbage, textString)
    categories_text = re.findall(parse_categories, textString)
    for i in categories_text:
        textString.replace(i, "")
    
    if len(re.findall(r"==external links==", textString))>0:
        external_link_text = textString.split("==external links==")[1]
        textString = textString.replace(external_link_text, "")


    ## Body
    text_split=textString.split("\n")
    temp_len=len(text_split)
    for i in range(len(text_split)):
        if i < len(text_split) and len(text_split[i])>2:
            if text_split[i][0:3]=="# 2":
                text_split.remove(text_split[i])
    temp_len2 = len(text_split)
    if temp_len!=temp_len2:
        countOf2+=1
    textString="\n".join(text_split)
    textString=re.sub(ref_garbage,"", textString)
    textString = re.sub(string_garbage, '', textString)    
    textString = re.sub(number_garbage, '', textString)
    textTokens = re.findall(token_reg, textString)
    stopTextTokens = [i for i in textTokens if i not in stopword_set]
    
    stopTextTokens = removeNumbers(stopTextTokens)
    stemTextTokens = stemmer.stemWords(stopTextTokens)
    for i in stemTextTokens:
        if (len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0) or (len(i)==1 and i in "0123456789"):
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
            if (len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0) or (len(i)==1 and i  in "0123456789"):
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
        # print(reference_text)
        content=[i[3]for i in reference_text]
        reference_text = " ".join(content)
        reference_text=re.findall(parse_references, reference_text)
        if len(reference_text)>0:
            refExtText=[i[1] for i in reference_text]
            # print(refExtText)
            refExtText = " ".join(refExtText)
            linkRef = re.sub(links_garbage, '', refExtText)
            numRef = re.sub(number_garbage, '', linkRef)
            refTokens = re.findall(token_reg, numRef)
            stopRefTokens = [i for i in refTokens if i not in stopword_set]
            stopRefTokens = removeNumbers(stopRefTokens)
            stemRefTokens = stemmer.stemWords(stopRefTokens)
            for i in stemRefTokens:
                if (len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0) or (len(i)==1 and i  in "0123456789"):
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
                if (len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0) or (len(i)==1 and i  in "0123456789"):
                    addCount2Index(i, totalCount, 'l')

def breakIndex(memory_factor=(1000*1000), threshold = 50):
    onlyfiles = [os.path.join(PATH_INDEX, f) for f in os.listdir(PATH_INDEX) if os.path.isfile(os.path.join(PATH_INDEX, f))]
    onlyfiles = sorted(onlyfiles)
    sizeSelected=[]
    sizeList=[]
    endCorr = []
    brokenFiles=[]
    for i in onlyfiles:
        if (os.path.getsize(i))/memory_factor>threshold and i[-4:]!="json":
            sizeSelected.append(i)
            sizeList.append((os.path.getsize(i))/memory_factor)
    countOfbreaks=0
    for id, file_path in enumerate(sizeSelected):
        factor = int(sizeList[id]//threshold)*2+1
        with open(file_path, 'r') as f:
            temp_index2divide = json.load(f)
            f.close()
        sorted_keysList=sorted(list(temp_index2divide.keys()))
        sizeOfNewfiles=int(len(sorted_keysList)//factor)
        for i in range(factor):
            countOfbreaks+=1
            newDictionary={}
            for j in sorted_keysList[i*sizeOfNewfiles:(i+1)*sizeOfNewfiles]:
                newDictionary.update({j:temp_index2divide[j]})
            new_file_name = file_path+"_"+str(i)
            end=sorted_keysList[((i+1)*sizeOfNewfiles)-1]
            endCorr.append((new_file_name.split("/")[-1], end))
            with open(new_file_name, 'w') as f:
                f.write(json.dumps(newDictionary, indent=0, separators=(",", ":")).replace("\n", ""))
                f.close()
        countOfbreaks+=1

        newDictionary={}
        for j in sorted_keysList[factor*sizeOfNewfiles:]:
            newDictionary.update({j:temp_index2divide[j]})
        new_file_name = file_path+"_"+str(factor)
        end=sorted_keysList[-1]
        endCorr.append((new_file_name.split("/")[-1], end))
        with open(new_file_name, 'w') as f:
            f.write(json.dumps(newDictionary, indent=0, separators=(",", ":")).replace("\n", ""))
            f.close()
        brokenFiles.append((file_path.split("/")[-1], countOfbreaks))

        
        os.remove(file_path)
    brokenHash = os.path.join(PATH_INDEX, "lastWord")
    with open(brokenHash, 'wb') as f:
        pkl.dump(endCorr, f)
        f.close()
    brokenFilesList = os.path.join(PATH_INDEX, "broken")
    with open(brokenFilesList, 'wb') as f:
        pkl.dump(brokenFiles, f)
        f.close()


#-----------------------------------------------------FREQ variable
freqD = 50000
freqT = 50000
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
                if (len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0 )or(len(i)==1 and i in "0123456789"):
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
            countOfText+=1
            text_1 = text.lower()
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
                with open("./progress_file.txt", "w") as f:
                    f.write(str(totalCount))
                    f.close()
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
    if os.path.isfile(file_path):
        with open(file_path, "r") as f:
            inverted_index = json.load(f)
            f.close()
        total_keys += len(inverted_index.keys())
breakIndex(1000, 100)

print("Total keys : {}".format(total_keys))
elapsed_time = time.time() - start_time
print("Total pages: {:,}".format(totalCount))
print("Elapsed time: {}".format(hms_string(elapsed_time)))
