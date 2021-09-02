import xml.etree.ElementTree as etree
import codecs
import csv
import time
import os
import re
import json
import nltk
import Stemmer
import pickle as pkl
# from gibberish_detector import detector
from tqdm import tqdm

PATH_WIKI_XML = '/home/starc/Downloads/'
PATH_CSV='/home/starc/IRE-Stuff/'
FILENAME_WIKI = 'data'


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


pathWikiXML = os.path.join(PATH_WIKI_XML, FILENAME_WIKI)

totalCount = 0
title = None
start_time = time.time()
count_ns=[]

inverted_index={}
# ss = SnowballStemmer(language='english')
stemmer = Stemmer.Stemmer('english')
id_correspondence={}
Detector = detector.create_from_model('big.model')

with open('stopwords.pkl', 'rb') as f:
    stopword_set = pkl.load(f)
    f.close()


contin=0
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
            if not title:
                print("title:", title)
                contin+=1
                continue
            title_1 = title.lower()
            temp_title = stemmer.stemWords(re.findall(r'[a-zA-Z0-9]+', title_1))
            for i in temp_title:
                if i not in stopword_set and len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                    stemmed_i = i
                    if stemmed_i not in inverted_index.keys():
                        inverted_index[stemmed_i]={'t':{totalCount:1}}
                    elif stemmed_i in inverted_index.keys() and 't' not in inverted_index[stemmed_i].keys():
                        inverted_index[stemmed_i]['t'] = {totalCount:1}
                    elif stemmed_i in inverted_index.keys() and totalCount not in inverted_index[stemmed_i]['t'].keys():
                        inverted_index[stemmed_i]['t'][totalCount]=1
                    else:
                        inverted_index[stemmed_i]['t'][totalCount]+=1

        elif tname == 'id' and not inrevision:
            id = int(elem.text)
        elif tname == 'ns':
            ns = int(elem.text)
        elif tname == 'text':
            text = elem.text
            if not text:
                contin+=1
                continue
            # stringOfRe = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
            text_1 = text.lower()
            
            string_cite = r"(\{\{cite web\|.*\|.*)(title=[^|]*)(\|.*\}\})"
            text = re.sub(string_cite, r"\2", text_1)
            
            string_image = r"(\[\[File:.*)(\|[^|]*)(\]\])"
            text_1 = re.sub(string_image, r"\2", text)

            string_garbage = r"(\{\{[^{}\[\]]*\}\})|(\[\[[^{}\[\]]*\]\])"
            text = re.sub(string_garbage, ' ', text_1)

            stringOfRe = r"(http://|https://|ftp://|smtp://)([a-z0-9.\-]+[.][a-z]{2,4})([^ \n]*\||[^ \n]*;|[^ \n]* |[^ \n]*|)"
            text_1 = re.sub(stringOfRe, ' ', text)
            
            text_split=text_1.split("\n")
            for i in range(len(text_split)):
                if len(text_split[i])>2:
                    if text_split[i][0:3]=="# 2" or text_split[i][0]=='&':
                        text_split[i]=""
            text="\n".join(text_split)

            text_1 = re.findall(r'([a-zA-Z0-9]+)', text)

            temp_text = stemmer.stemWords(text_1)

            for i in temp_text:
                if i not in stopword_set and len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                    stemmed_i = i#ss.stem(i)
                    if stemmed_i not in inverted_index.keys():
                        temp={'b':{totalCount:1}}
                        inverted_index[stemmed_i]=temp
                    elif stemmed_i in inverted_index.keys() and 'b' not in inverted_index[stemmed_i].keys():
                        inverted_index[stemmed_i]['b'] = {totalCount:1}
                    elif stemmed_i in inverted_index.keys() and totalCount not in inverted_index[stemmed_i]["b"].keys():
                        inverted_index[stemmed_i]['b'][totalCount]=1
                    else:
                        inverted_index[stemmed_i]['b'][totalCount]+=1

        elif tname == 'page':
            count_ns.append(ns)
            orig_text=text
                        
            totalCount += 1
            if totalCount%10000==0:
                print(totalCount)               
        elem.clear()


# count=0
# # for i in inverted_index.keys():
# #     if Detector.is_gibberish(i):
# #         count+=1
# print(count)
print("continue count:", contin)
print(len(inverted_index.keys()))
print(inverted_index.keys())
with open("inverted_index.json", "w") as f:
    f.write(json.dumps(inverted_index, indent=0, separators=(",", ":")).replace("\n", ""))
    f.close()

with open("id_correspondence.json", "w") as f:
    json.dump(id_correspondence, f, indent=0)
    f.close()


elapsed_time = time.time() - start_time
print("Total pages: {:,}".format(totalCount))
print("Elapsed time: {}".format(hms_string(elapsed_time)))