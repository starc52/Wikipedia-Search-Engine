import xml.etree.ElementTree as etree
import time
import os
import re
import json
import Stemmer
import pickle as pkl
import sys


PATH_WIKI_XML = sys.argv[1]
PATH_INDEX = os.path.join(sys.argv[2], "index.txt")
PATH_STAT = sys.argv[3]



pathWikiXML = PATH_WIKI_XML

totalCount = 0
title = None
start_time = time.time()
count_ns=[]

inverted_index={}
# ss = SnowballStemmer(language='english')
stemmer = Stemmer.Stemmer('english')

with open('stopwords.pkl', 'rb') as f:
    stopword_set = pkl.load(f)
    f.close()
stopword_set.add('category')

temp_words_uniq=set([])

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

def addCount2Index(word, totalCount,field):
    global inverted_index
    if word not in inverted_index.keys():
        inverted_index[word]={field:{totalCount:1}}
    elif word in inverted_index.keys() and field not in inverted_index[word].keys():
        inverted_index[word][field] = {totalCount:1}
    elif word in inverted_index.keys() and totalCount not in inverted_index[word][field].keys():
        inverted_index[word][field][totalCount]=1
    else:
        inverted_index[word][field][totalCount]+=1

def fineTuneRegex(listOfstrings):
    returnListOfStrings=["" for i in range(len(listOfstrings))]
    for i in range(len(listOfstrings)):
        if listOfstrings[i][0]=="{":
            bracket="{"
            inBracket="}"
        else:
            bracket="["
            inBracket="}"
        stack=0
        for j in range(len(listOfstrings[i])):
            if listOfstrings[i][j]==bracket and listOfstrings[i][j+1]==bracket:
                j+=1
                stack+=1
            # print(listOfstrings[i], j)
            if listOfstrings[i][j]==inBracket and listOfstrings[i][j+1]==inBracket:
                j+=1
                stack-=1
                if stack ==0:
                    returnListOfStrings[i]=listOfstrings[i][:j+1]
                    break
    while "" in returnListOfStrings:
        returnListOfStrings.remove("")
    return returnListOfStrings

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
                # print("title:", title)
                continue
            title_1 = title.lower()
            for i in title_1.split(" "):
                temp_words_uniq.add(i)
            temp_title_1=re.findall(r'[a-zA-Z0-9]+', title_1)
            temp_title=[i for i in temp_title_1 if i not in stopword_set]
            temp_title = stemmer.stemWords(temp_title)
#------------------------------- Adding Title tokens to the index
            for i in temp_title:
                if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                    stemmed_i = i
                    # temp_words_uniq.add(stemmed_i)
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
            for i in text_1.split(" "):
                temp_words_uniq.add(i)
            complete_text = text_1

            text_split=text_1.split("\n")
            for i in range(len(text_split)):
                if len(text_split[i])>2:
                    if text_split[i][0:3]=="# 2": #or text_split[i][0]=='&':
                        text_split[i]=""
            text="\n".join(text_split)

            string_garbage = r"(\[\[[^\[\]]*?\]\])|(\{\{[^{}]*?\}\})"
            text_1 = re.sub(string_garbage, '', text)
        
            text = re.findall(r'([a-zA-Z0-9]+)', text_1)

            text_1 = [i for i in text if i not in stopword_set]

            temp_text = stemmer.stemWords(text_1)
#---------------------------- Adding body tokens to inverted index
            for i in temp_text:
                if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                    stemmed_i = i#ss.stem(i)
                    addCount2Index(stemmed_i, totalCount, 'b')
            
            text_2 = complete_text

            parse_categories =r"\[\[category:.*?\]\]"
            temp_cat_reg = re.findall(parse_categories, text_2)
            if len(temp_cat_reg)>0:
                # text_2_cat = [i[0] for i in temp_cat_reg]        
                text_2 = " ".join(temp_cat_reg)
                text_2_cat = re.findall(r'([a-zA-Z0-9]+)', text_2)
                
                text_2 = [i for i in text_2_cat if i not in stopword_set]
                
                temp_cat_text = stemmer.stemWords(text_2)
#-------------------------Adding Category tokens to the inverted index
                for i in temp_cat_text:
                    if len(i)<20  and len(i)!=0:
                        stemmed_i = i
                        addCount2Index(stemmed_i, totalCount, 'c')

            text_3 = complete_text

            parse_infobox = r"(\{\{infobox.*)(\|.*)(\|.*?\}\})"
            text_3_info = re.findall(parse_infobox, text_3)
            if len(text_3_info)>0:
                text_3 = [" ".join(i) for i in text_3_info]
                text_3 = " ".join(fineTuneRegex(text_3_info))
                text_3_info = re.findall(r'([a-zA-Z0-9]+)', text_3)

                text_3 = [i for i in text_3_info if i not in stopword_set]
                
                temp_info_text = stemmer.stemWords(text_3)
#---------------------------- Adding infobox tokens to the inverted index            
                for i in temp_info_text:
                    if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                        stemmed_i = i
                        addCount2Index(stemmed_i, totalCount, 'i')
                
            text_4 = complete_text
            if len(re.findall(r"==references==", text_4))>0 and len(re.findall(r"==external links==", text_4))>0:
                text_4_ref = text_4.split("==references==")[1]
                text_5_extlin = text_4.split("==external links==")[1]
                text_4 = text_4_ref.replace(text_5_extlin, "")
                parse_references = r"(\*?\{\{.*\|)(title=.*?)(\|.*?\}\})"
                temp_ref_reg=re.findall(parse_references, text_4)
                if len(temp_ref_reg)>0:
                    text_4_ref=[i[1] for i in temp_ref_reg]

                    text_4 = " ".join(text_4_ref)

                    text_4_ref = re.findall(r'([a-zA-Z0-9]+)', text_4)

                    text_4 = [i for i in text_4_ref if i not in stopword_set]

                    temp_ref_text = stemmer.stemWords(text_4)
#------------------------ Adding reference tokens to the inverted index
                    for i in temp_ref_text:
                        if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                            stemmed_i = i
                            addCount2Index(stemmed_i, totalCount, 'r')

                parse_ext_links = r"( *\* *\[[^ ]*)(.*?)(\])"
                temp_ext_reg=re.findall(parse_ext_links, text_5_extlin)
                if len(temp_ext_reg)>0:
                    text_5 = [i[1] for i in temp_ext_reg]
                    text_5_extlin = " ".join(text_5)
                    text_5 = re.findall(r'([a-zA-Z0-9]+)', text_5_extlin)
                    text_5_extlin = [i for i in text_5 if i not in stopword_set]
                    temp_extlin_text = stemmer.stemWords(text_5_extlin)
#--------------------------- Adding external link tokens to the inverted index
                    for i in temp_extlin_text:
                        if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                            stemmed_i = i
                            addCount2Index(stemmed_i, totalCount, 'l')
            
            elif len(re.findall(r"==references==", text_4))>0:
                text_4_ref = text_4.split("==references==")[1]
                parse_references = r"(\*?\{\{.*\|)(title=.*?)(\|.*?\}\})"
                temp_ref_reg=re.findall(parse_references, text_4_ref)
                if len(temp_ref_reg)>0:
                    text_4_ref=[i[1] for i in temp_ref_reg]

                    text_4 = " ".join(text_4_ref)

                    text_4_ref = re.findall(r'([a-zA-Z0-9]+)', text_4)

                    text_4 = [i for i in text_4_ref if i not in stopword_set]

                    temp_ref_text = stemmer.stemWords(text_4)
#------------------------ Adding reference tokens to the inverted index
                    for i in temp_ref_text:
                        if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                            stemmed_i = i
                            addCount2Index(stemmed_i, totalCount, 'r')
            elif len(re.findall(r"==external links==", text_4))>0:
                text_5_extlin = text_4.split("==external links==")[1]
                parse_ext_links = r"( *\* *\[[^ ]*)(.*?)(\])"
                temp_ext_reg=re.findall(parse_ext_links, text_5_extlin)
                if len(temp_ext_reg)>0:
                    text_5 = [i[1] for i in temp_ext_reg]
                    text_5_extlin = " ".join(text_5)
                    text_5 = re.findall(r'([a-zA-Z0-9]+)', text_5_extlin)
                    text_5_extlin = [i for i in text_5 if i not in stopword_set]
                    temp_extlin_text = stemmer.stemWords(text_5_extlin)
#--------------------------- Adding external link tokens to the inverted index
                    for i in temp_extlin_text:
                        if len(i)<20 and i[-3:]!="jpg" and i[-4:]!="jpeg" and i[-3:]!="png" and len(i)!=0:
                            stemmed_i = i
                            addCount2Index(stemmed_i, totalCount, 'l')

        elif tname == 'page':
            count_ns.append(ns)
            orig_text=text
                        
            totalCount += 1
            # if totalCount%10000==0:
            #     print(totalCount)               
        elem.clear()


with open(PATH_INDEX, "w") as f:
    f.write(json.dumps(inverted_index, indent=0, separators=(",", ":")).replace("\n", ""))
    f.close()

# print(len(set(temp_words_uniq)))
# print(len(inverted_index.keys()))
with open(PATH_STAT, 'w') as f:
    f.write(str(len(set(temp_words_uniq))) + "\n"+str(len(inverted_index.keys())))

# elapsed_time = time.time() - start_time
# print("Total pages: {:,}".format(totalCount))
# print("Elapsed time: {}".format(hms_string(elapsed_time)))