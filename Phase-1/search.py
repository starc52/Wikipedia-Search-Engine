import time
import os
import re
import json
import Stemmer
import pickle as pkl
import sys
find_lst = []
stemmer = Stemmer.Stemmer('english')
PATH_INDEX = os.path.join(sys.argv[1], "index.txt")
with open(PATH_INDEX, 'r') as f:
    index = json.load(f)
    f.close()
find_tag = []

prompt = sys.argv[2]
result = {}

query_lst = prompt.split(" ")

for element in query_lst:
    tmp = element.split(":")
    if len(tmp)>1:
        find_lst.append(tmp[1])
        find_tag.append(tmp[0])
    else:
        find_lst.append(tmp[0])

for word in find_lst:
    l_docs = []
    c_docs = []
    i_docs = []
    t_docs = []
    b_docs = []
    r_docs = []
    s_word = stemmer.stemWord(word.lower())

    if s_word  not in index.keys():
        result[word] = {"title": [], "text": [], "references": [], "external links": [], "categories": [], "infobox": []}        
    else:
        word_dict = index[s_word]
        plain_field_dict = {}
        
        if 't' in word_dict.keys():
            t_docs+=list(word_dict['t'])
        plain_field_dict["title"] = t_docs

        if 'b' in word_dict.keys():
            b_docs+=list(word_dict['b'])
        plain_field_dict["body"] = t_docs

        if 'r' in word_dict.keys():
            r_docs+=list(word_dict['r'])
        plain_field_dict["references"] = r_docs

        if 'l' in word_dict.keys():
            l_docs+=list(word_dict['l'])
        plain_field_dict["external links"] = l_docs

        if 'c' in word_dict.keys():
            c_docs+=list(word_dict['c'])
        plain_field_dict["categories"] = c_docs

        if 'i' in word_dict.keys():
            i_docs+=list(word_dict['i'])
        plain_field_dict["infobox"] = i_docs

        result[word] = plain_field_dict

print(json.dumps(result, indent=2))
