import xml.etree.ElementTree as etree
import codecs
import csv
import time
import os
import re
import json
import nltk
from nltk import word_tokenize
from nltk.stem import SnowballStemmer
import Stemmer
import pickle as pkl
from gibberish_detector import detector
from tqdm import tqdm

# http://www.ibm.com/developerworks/xml/library/x-hiperfparse/

PATH_WIKI_XML = '/home/starc/Downloads/'
PATH_CSV='/home/starc/IRE-Stuff/'
FILENAME_WIKI = 'data'
FILENAME_ARTICLES = 'articles.csv'
FILENAME_REDIRECT = 'articles_redirect.csv'
FILENAME_TEMPLATE = 'articles_template.csv'
ENCODING = "utf-8"


# Nicely formatted time string
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
pathArticles = os.path.join(PATH_CSV, FILENAME_ARTICLES)
pathArticlesRedirect = os.path.join(PATH_CSV, FILENAME_REDIRECT)
pathTemplateRedirect = os.path.join(PATH_CSV, FILENAME_TEMPLATE)

totalCount = 0
articleCount = 0
redirectCount = 0
templateCount = 0
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

stopword_set.add("redirect")
stopword_set.add("category")
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
            title = re.sub(r'([^a-zA-Z0-9 ])', ' ', title_1)
            title_1 = re.sub(r'([ ]+)', ' ', title)
            title = title_1
            temp_title = stemmer.stemWords(title.split(" ")) #word_tokenize(title)
            for i in temp_title:
                if i not in stopword_set and len(i)<30 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                    stemmed_i = i#ss.stem(i)
                    if stemmed_i not in inverted_index.keys():
                        temp={totalCount:[1,0]}
                        inverted_index[stemmed_i]=temp
                        # print(totalCount)
                    elif stemmed_i in inverted_index.keys() and totalCount not in inverted_index[stemmed_i].keys():
                        inverted_index[stemmed_i][totalCount] = [1,0]
                    else:
                        inverted_index[stemmed_i][totalCount][0]+=1
            # title = re.sub(r'#REDIRECT |#redirect ', '', str(title))
        elif tname == 'id' and not inrevision:
            id = int(elem.text)
        elif tname == 'ns':
            ns = int(elem.text)
        elif tname == 'text':
            text = elem.text
            if not text:
                # print("text:", text)
                contin+=1
                continue
            # stringOfRe = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
            text_1 = text.lower()
            stringOfRe = r"(http|https|ftp|smtp)://(([^ \n]*?),|([^ \n]*?);|([^ \n]*? )|([^ \n]*?|))"
            text = re.sub(stringOfRe, ' ', text_1)
            text_1 = re.sub(r'([^a-zA-Z0-9 ])', ' ', text)
            text = re.sub(r'([ ]+)', ' ', text_1)
            # print(text)
            # if len(orig_text)-len(text)<5:
            #     print(orig_text, text, totalCount)
            
            temp_text = stemmer.stemWords(text.split(" ")) #word_tokenize(text)
            for i in temp_text:
                if i not in stopword_set and len(i)<30 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                    stemmed_i = i#ss.stem(i)
                    if stemmed_i not in inverted_index.keys():
                        temp={totalCount:[0,1]}
                        inverted_index[stemmed_i]=temp
                    elif stemmed_i in inverted_index.keys() and totalCount not in inverted_index[stemmed_i].keys():
                        inverted_index[stemmed_i][totalCount] = [0,1]
                    else:
                        inverted_index[stemmed_i][totalCount][1]+=1
        elif tname == 'page':
            count_ns.append(ns)
            # print(text)
            orig_text=text
                        
            totalCount += 1
            if totalCount%10000==0:
                print(totalCount)               
        elem.clear()


count=0
for i in inverted_index.keys():
    if Detector.is_gibberish(i):
        print(i)
        count+=1
print(count)
print("continue count:", contin)
# print(inverted_index.keys())
print(len(inverted_index.keys()))
with open("inverted_index.json", "w") as f:
    f.write(json.dumps(inverted_index, indent=0, separators=(",", ":")).replace('\n', ''))
    f.close()

with open("id_correspondence.json", "w") as f:
    json.dump(id_correspondence, f, indent=0)
    f.close()


elapsed_time = time.time() - start_time
# print(set(count_ns))
print("Total pages: {:,}".format(totalCount))
print("Template pages: {:,}".format(templateCount))
print("Article pages: {:,}".format(articleCount))
print("Redirect pages: {:,}".format(redirectCount))
print("Elapsed time: {}".format(hms_string(elapsed_time)))