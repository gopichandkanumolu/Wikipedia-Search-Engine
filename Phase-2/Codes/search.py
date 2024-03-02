#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pickle
import re
import time
import Stemmer
import time
from collections import defaultdict
import sys
import numpy as np
import itertools
from tqdm import tqdm


# In[2]:


dest_dir = "./final_files/"
id_title_map_path = dest_dir + "title_info.txt"


# In[3]:


def preprocess_text(text, remove_links=False):
    cleaned_text=text.lower().strip()
    if(remove_links):
        cleaned_text= re.sub(r'https?://\S+|www\.\S+','', cleaned_text)
    cleaned_text = re.sub('[^a-zA-Z0-9 ]+',' ', cleaned_text)
    cleaned_text=cleaned_text.strip()
    tokens=cleaned_text.split()
    tokens=[token for token in tokens if token not in stop_words]
    cleaned_text_tokens=stemmer.stemWords(tokens)
    return cleaned_text_tokens


# In[4]:


def parse_text_posting(word_posting):
    posting = {}
    word_posting = re.sub(r'([tbicrl])', r':\1,', word_posting)
    for doc in word_posting.split(';'):
        # 233492-:t,1:b,1:i,1
        doc = doc.strip()
        if doc!='':
            doc_no, cat_str = doc.split('-') # ["233492", ":t,1:b,1:i,1"]
            cat_str = cat_str.strip().strip(':') # t,1:b,1:i,1
            for category in cat_str.split(':'): # ["t,1", "b,1", "i,1"]
                cat, freq = category.strip().split(',') # ["t", "1"]
                cat = cat.strip() # "t"
                freq = int(freq.strip()) # 1
                
                if cat not in posting:
                    posting[cat] = {doc_no: freq}
                else:
                    posting[cat][doc_no] = freq
    return posting


# In[5]:


def binary_search_get_entry(file_pointer, token, token_type="token"):
    start = 0
    end = len(file_pointer.readlines())
    posting = {}
    while True:
        file_pointer.seek(0)
        offset = int((end - start) / 2)
        mid = start + offset
        
        if mid==0:
            entry = file_pointer.readline()
        else:
            entry = list(itertools.islice(file_pointer, mid-1, mid))[0]
        
        word, word_posting = entry.split(':', 1)
        token = str(token)

        if(token_type=="title"):
            word = int(word)
            token = int(token.strip())
            
        # print("start: ", start, "\tmid: ", mid, "\tend: ", end, "\tword: ", word)
        if word==token:
            # print("Found at: ", mid)
            if token_type=="title":
                return word_posting.strip()
            else:
                return parse_text_posting(word_posting)
        elif start==(end-1):
            break
        elif word < token:
            start = mid + 1
        else:
            end = mid
            
    return posting


# In[6]:


def find_index_file(file_pointer, token, token_type="token"):
    start = 0
    end = len(file_pointer.readlines())
    while True:
        file_pointer.seek(0)
        offset = int((end - start) / 2)
        mid = start + offset
        
        if mid==0:
            entry = file_pointer.readline()
        else:
            entry = list(itertools.islice(file_pointer, mid-1, mid))[0]
        
        word, file_id = entry.split('=', 1)
        start_word, end_word = word.split('_')
        start_word = start_word.strip()
        end_word = end_word.strip()
        token = str(token)
        
        if(token_type=="title"):
            start_word = int(start_word)
            end_word = int(end_word)
            token = int(token.strip())
        
        # print("start: {}\tmid: {}\tend: {}\tstart_word: {}\tend_word: {}\ttoken: {}".format(start, mid, end, start_word, end_word, token))
        
        if token>=start_word and token<=end_word:
            return mid
        elif start==(end-1):
            break
        elif end_word < token:
            start = mid + 1
        else:
            end = mid
            
    return -1


# In[7]:


def field_query(search_string):
    tag_spans=[i.span() for i in re.finditer('[tibcrl]{1}:',search_string.lower())]
    doc_score={}
    if tag_spans!=[]:
        for idx,ts in enumerate(tag_spans):
            start = ts[1]
            if idx<len(tag_spans)-1:
                end = tag_spans[idx+1][0]-1
            else:
                end=len(search_string)

            content=search_string[start:end]
            tag=search_string[ts[0]:ts[1]-1]
            ax=query(content)
            doc_score.update(ax)
    return doc_score


# In[8]:


def query(search_string):
    tokens=preprocess_text(search_string)
    
    token_count_dic={}
    for token in tokens:
        if token not in token_count_dic:
            token_count_dic[token]=1
        else:
            token_count_dic[token]+=1
    
    data = {}
    for token in token_count_dic:
        start_letter = token[0]
        fp = open(dest_dir + start_letter + "_info.txt", 'r')
        file_id = find_index_file(fp, token)
        fp.close()
        if(file_id!=-1):
            fp = open(dest_dir + start_letter + "_" + str(file_id)+".txt")
            data[token] = binary_search_get_entry(fp, token)
            fp.close()
    
    tf_dict={}
    common_tags=set()
    for idx,token in enumerate(tokens):
        tf=token_count_dic[token]#/denominator
        tf_dict[token]=tf
        try:
            token_tags=set(data[token].keys())
            if idx==0:
                common_tags.update(token_tags)
            else:
                common_tags=common_tags.intersection(token_tags) # work
                #common_tags=common_tags.union(token_tags)
        except:
            None
    
    common_ids=dict()    
    for tag in common_tags:
        dummy=set()
        for idx,token in enumerate(tokens):
            try:
                ids=set(data[token][tag].keys())
                if idx==0:
                    dummy.update(ids)
                else:
                    dummy=dummy.intersection(ids) # work
                    #dummy=dummy.union(ids)
            except:
                None

        if len(dummy)>0:
            common_ids[tag]=dummy
        
    idf_dict={}
    for token in tokens:
        ts=data[token]
        docs=set()
        for t in ts:
            docs.update(set(data[token][t].keys()))
            
        idf_dict[token]=np.log(len(data)/len(docs)+1)
        
    #weights={'t':20,'b':0.3,'i':0.2,'c':0.1,'r':0.01,'l':0.01}
    weights={'t':10,'b':0.2,'i':0.2,'c':0.1,'r':0.01,'l':0.01}
    scores={}
    for tag in common_ids:
        ids=common_ids[tag]
        for id_ in ids:
            tf_idf=0
            for word in tokens:
                try:
                    tf=data[word][tag][id_]
                    idf=idf_dict[word]
                    tf_idf+=weights[tag]*tf*idf
                except:
                    None

            scores[id_]=tf_idf
    return scores


# In[9]:


def search(search_string):
    # print(search_string)
    tag_spans=[i.span() for i in re.finditer('[tibcrl]{1}:',search_string.lower())]
    if tag_spans==[]:
        # print('searching plain query')
        result=query(search_string)
    else:
        # print('searching field query')
        result=field_query(search_string)
    return result


# In[10]:


aa = []
with open("queries.txt", 'r') as fp:
    for line in fp.readlines():
        line = line.strip()
        aa.append(line)


# In[11]:


get_ipython().run_cell_magic('time', '', 'stemmer = Stemmer.Stemmer(\'english\')\nstop_words={\'i\', \'me\', \'my\', \'myself\', \'we\', \'our\', \'ours\', \'ourselves\', \'you\', "you\'re", "you\'ve", "you\'ll", "you\'d", \'your\', \'yours\', \'yourself\', \'yourselves\', \'he\', \'him\', \'his\', \'himself\', \'she\', "she\'s", \'her\', \'hers\', \'herself\', \'it\', "it\'s", \'its\', \'itself\', \'they\', \'them\', \'their\', \'theirs\', \'themselves\', \'what\', \'which\', \'who\', \'whom\', \'this\', \'that\', "that\'ll", \'these\', \'those\', \'am\', \'is\', \'are\', \'was\', \'were\', \'be\', \'been\', \'being\', \'have\', \'has\', \'had\', \'having\', \'do\', \'does\', \'did\', \'doing\', \'a\', \'an\', \'the\', \'and\', \'but\', \'if\', \'or\', \'because\', \'as\', \'until\', \'while\', \'of\', \'at\', \'by\', \'for\', \'with\', \'about\', \'against\', \'between\', \'into\', \'through\', \'during\', \'before\', \'after\', \'above\', \'below\', \'to\', \'from\', \'up\', \'down\', \'in\', \'out\', \'on\', \'off\', \'over\', \'under\', \'again\', \'further\', \'then\', \'once\', \'here\', \'there\', \'when\', \'where\', \'why\', \'how\', \'all\', \'any\', \'both\', \'each\', \'few\', \'more\', \'most\', \'other\', \'some\', \'such\', \'no\', \'nor\', \'not\', \'only\', \'own\', \'same\', \'so\', \'than\', \'too\', \'very\', \'s\', \'t\', \'can\', \'will\', \'just\', \'don\', "don\'t", \'should\', "should\'ve", \'now\', \'d\', \'ll\', \'m\', \'o\', \'re\', \'ve\', \'y\', \'ain\', \'aren\', "aren\'t", \'couldn\', "couldn\'t", \'didn\', "didn\'t", \'doesn\', "doesn\'t", \'hadn\', "hadn\'t", \'hasn\', "hasn\'t", \'haven\', "haven\'t", \'isn\', "isn\'t", \'ma\', \'mightn\', "mightn\'t", \'mustn\', "mustn\'t", \'needn\', "needn\'t", \'shan\', "shan\'t", \'shouldn\', "shouldn\'t", \'wasn\', "wasn\'t", \'weren\', "weren\'t", \'won\', "won\'t", \'wouldn\', "wouldn\'t"}\ntitles_dict = {}\nindex = -1\ntime_taken = []\nfor search_query in tqdm(aa):\n    st = time.time()\n    index += 1\n    titles_dict[index] = {}\n#     search_query= aa[1]\n    # search_query=\'t:sachin tendulkar c:world cup i:2018\'\n\n    scores=search(search_query)\n    scores=dict(sorted(scores.items(), key=lambda item: item[1],reverse=True))\n    outs=[key for key in list(scores.keys())[:10]]\n\n    for ind, title in enumerate(outs):\n        fp = open(dest_dir + "title_info.txt", \'r\')\n        file_id = find_index_file(fp, title, token_type="title")\n        fp.close()\n        if(file_id!=-1):\n            fp = open(dest_dir +  "title_" + str(file_id)+".txt")\n            titles_dict[index][ind] = (title, binary_search_get_entry(fp, title, token_type="title"))\n            fp.close()\n    et = time.time()\n    time_taken.append(et-st)\n\noutput_str = ""\n\nfor index in titles_dict:    \n    for ind in titles_dict[index]:\n        output_str += titles_dict[index][ind][0] + "\\t-\\t" + titles_dict[index][ind][1] +"\\n"\n    output_str += str(time_taken[index])+"\\n"\n    output_str += "\\n\\n"\n\nwith open("queries_op.txt", \'w\') as fp:\n    fp.write(output_str)\n')

