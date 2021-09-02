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
ss = SnowballStemmer(language='english')
id_correspondence={}
Detector = detector.create_from_model('big.model')

with open('stopwords.pkl', 'rb') as f:
    stopword_set = pkl.load(f)
    f.close()

# with codecs.open(pathArticles, "w", ENCODING) as articlesFH, \
#         codecs.open(pathArticlesRedirect, "w", ENCODING) as redirectFH, \
#         codecs.open(pathTemplateRedirect, "w", ENCODING) as templateFH:
#     articlesWriter = csv.writer(articlesFH, quoting=csv.QUOTE_MINIMAL)
#     redirectWriter = csv.writer(redirectFH, quoting=csv.QUOTE_MINIMAL)
#     templateWriter = csv.writer(templateFH, quoting=csv.QUOTE_MINIMAL)

#     articlesWriter.writerow(['id', 'title', 'redirect', 'text'])
#     redirectWriter.writerow(['id', 'title', 'redirect'])
#     templateWriter.writerow(['id', 'title'])
for event, elem in etree.iterparse(pathWikiXML, events=('start', 'end')):
    tname = strip_tag_name(elem.tag)
    
    temp_title_count={}
    temp_redirect_count={}
    temp_text_count={}

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
            # title = re.sub(r'#REDIRECT |#redirect ', '', str(title))
        elif tname == 'id' and not inrevision:
            id = int(elem.text)
        elif tname == 'redirect':
            redirect = elem.attrib['title']
            # redirect = re.sub(r'#REDIRECT |#redirect ', '', str(redirect))

        elif tname == 'ns':
            ns = int(elem.text)
        elif tname == 'text':
            text = elem.text
            text = re.sub(r'#REDIRECT|#redirect', '', str(text))

        elif tname == 'page':
            totalCount += 1
            # text = elem.text
            count_ns.append(ns)
            # if len(text)>30:
            # stringOfRe = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
            title = re.sub(r'([^a-zA-Z0-9 ])', '', title)
            text = re.sub(r'([^a-zA-Z0-9 ])', '', text)
            # redirect = re.sub(r'([^a-zA-Z0-9 ])', '', redirect)
            
            temp_title = title.split(" ") #word_tokenize(title)
            for i in temp_title:
                if i not in stopword_set and len(i)<30:
                    stemmed_i = ss.stem(i)
                    if stemmed_i in temp_title_count.keys():
                        temp_title_count[stemmed_i]+=1
                    else:
                        temp_title_count[stemmed_i]=1
            set_temp_title = list(temp_title_count)
            
            # temp_redirect = word_tokenize(redirect)
            # for i in temp_redirect:
            #     if i not in stopword_set and len(i)<30:
            #         stemmed_i=ss.stem(i)
            #         if stemmed_i in temp_redirect_count.keys():
            #             temp_redirect_count[stemmed_i]+=1
            #         else:
            #             temp_redirect_count[stemmed_i]=1
            
            # set_temp_redirect = list(temp_redirect_count)
            
            
            temp_text = text.split(" ") #word_tokenize(text)

            for i in temp_text:
                if i not in stopword_set and len(i)<30:
                    stemmed_i=ss.stem(i)
                    if stemmed_i in temp_text_count.keys():
                        temp_text_count[stemmed_i]+=1
                    else:
                        temp_text_count[stemmed_i]=1
            
            set_temp_text = list(temp_text_count)
            all_keys = set(list(temp_text_count)).union(set(list(temp_title_count)))
            # all_keys = set(list(temp_text_count)).union(set(list(temp_title_count)).union(set(list(temp_redirect_count))))
            all_docStr = ['' for i in range(len(all_keys))]
            id_correspondence[totalCount]=id
            for key in all_keys:
                docID_string=''
                if key in temp_title_count.keys():
                    docID_string=str(temp_title_count[key])+','
                if key in temp_text_count.keys():
                    docID_string=docID_string+str(temp_text_count[key])
                # if key in temp_redirect_count.keys():
                #     docID_string=docID_string+'r'+str(temp_redirect_count[key])
                
                docID_string=docID_string+'-'+str(totalCount)
                if key in inverted_index.keys():
                    inverted_index[key]=inverted_index[key]+"|"+docID_string
                else:
                    inverted_index[key]=docID_string
            if totalCount%1000==0:
                print(totalCount)               
        elem.clear()

count=0
for i in inverted_index.keys():
    if Detector.is_gibberish(i):
        count+=1

print(count)

print(len(inverted_index.keys()))
with open("inverted_index.json", "w") as f:
    json.dump(inverted_index, f, indent=0)
    f.close()

with open("id_correspondence.json", "w") as f:
    json.dump(id_correspondence, f, indent=0)
    f.close()


elapsed_time = time.time() - start_time
print(set(count_ns))
print("Total pages: {:,}".format(totalCount))
print("Template pages: {:,}".format(templateCount))
print("Article pages: {:,}".format(articleCount))
print("Redirect pages: {:,}".format(redirectCount))
print("Elapsed time: {}".format(hms_string(elapsed_time)))