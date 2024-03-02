#!pip install pystemmer
import pickle
import re
import time
import Stemmer
import time
from collections import defaultdict
import sys

index_file_path=sys.argv[1]
#search_query=sys.argv[1]
search_query=' '.join(sys.argv[2:])

stemmer = Stemmer.Stemmer('english')
stop_words={'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"}

with open(index_file_path,'rb') as fp:
    data=pickle.load(fp)

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

def query(search_string):
    tokens=preprocess_text(search_string)
    #print(tokens)
    common_tags=set()
    for idx,token in enumerate(tokens):
        token_tags=set(data[token].keys())
        if idx==0:
            common_tags.update(token_tags)
        else:
            common_tags=common_tags.intersection(token_tags)
            
    #print(common_tags)
    
    common_ids=dict()
    for tag in common_tags:
        dummy=set()
        for idx,token in enumerate(tokens):
            ids=set(data[token][tag].keys())
            if idx==0:
                dummy.update(ids)
            else:
                dummy=dummy.intersection(ids)
        if len(dummy)>0:
            common_ids[tag]=dummy
            
    #print(common_ids) 
    return common_ids

def field_query(search_string):
    tag_spans=[i.span() for i in re.finditer('[tibcrl]{1}:',search_string.lower())]
    tag_words_dict={}
    if tag_spans!=[]:
        for idx,ts in enumerate(tag_spans):
            start = ts[1]
            if idx<len(tag_spans)-1:
                end = tag_spans[idx+1][0]-1
            else:
                end=len(search_string)

            content=search_string[start:end]
            tag=search_string[ts[0]:ts[1]-1]
            tag_words_dict[tag]=query(content).get(tag,{})
            
    return tag_words_dict

def search(search_string):
    tag_spans=[i.span() for i in re.finditer('[tibcrl]{1}:',search_string.lower())]
    if tag_spans==[]:
        result=query(search_string)
    else:
        result=field_query(search_string)
    print(result)

#search_query= 't:World Cup i:2018 c:Football'
search(search_query)