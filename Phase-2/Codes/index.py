#!/usr/bin/env python
# Importing Libraries
import time
st=time.time()
import re
import Stemmer
import xml.sax
from collections import defaultdict
import json
import bz2
import pickle
from collections import OrderedDict

### =========================== parameters ============================
pl={}
c=0
num_pages = 0
id_title_map = {}
dump_path="./enwiki-20220820-pages-articles-multistream.xml.bz2"
index_path = './'
inverted_stat_path = './'
### ===================================================================

# Stemmer and Stopwords
stemmer = Stemmer.Stemmer('english')
stop_words={'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't", 'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"}

# Preprocessing
external_links_pattern = re.compile(r'[=]{2,}[ ]*external links[ ]*[=]{2,}|[=]{2,}[ ]*see also[ ]*[=]{2,}')
reference_pattern = re.compile(r'[=]{2,}references[=]{2,}|[=]{2,}notes[=]{2,}|[=]{2,}bibliography[=]{2,}')
category_pattern = re.compile(r'\[{2,}category.*\]{2,}')


def preprocess_text(text, remove_links=False):
    cleaned_text=text.lower().strip()
    global c
#     c+=len(cleaned_text.split())
    if(remove_links):
        cleaned_text= re.sub(r'https?://\S+|www\.\S+','', cleaned_text)
    cleaned_text = re.sub('[^a-zA-Z0-9 ]+',' ', cleaned_text)
    cleaned_text=cleaned_text.strip()
    tokens=cleaned_text.split()
    c+=len(tokens)
    tokens=[token for token in tokens if token not in stop_words]
    cleaned_text_tokens=stemmer.stemWords(tokens)
    return cleaned_text_tokens


def process_links(patterns, text):
    references = ''
    for pattern in patterns:
        if pattern in text:
            output = text.split(pattern)
            text.replace(pattern, "")
            if(len(output)>1):
                temp = output[1].split('\n')
                for line in temp:
                    if line!='':
                        references += line+"\n"
                        text.replace(line, "")
                    else:
                        break
    return references, text

def extract_useful_info(id_,title,text,ns):
    ns=ns.strip()
    doc_id=id_
    
    ### Infobox extraction
    infobox = re.findall(r'{{Infobox[\s\S]*?^}}$',text,re.MULTILINE)
    for match in infobox:
        text = text.replace(match, '')
    infobox = '\n'.join(infobox).replace('{{Infobox','')
    infbx=[]
    for seq in infobox.split('\n'):
        infbx+=seq.split('=')[1:]
    infobox=' '.join(infbx)
    
    ### Category extraction
    category = re.findall(category_pattern,text)
    for cat in category:
        text = text.replace(cat, '')
    category = '\n'.join(category)
    
    ### External Links extraction
    external_links, text = process_links(['==External links==', '==See also==', '==Further reading=='], text)
    
    ### References extraction
    references, text = process_links(["==References==", '==Notes==', '==Bibliography=='], text)
    
    ### Body text
    if ns=='0':
        body_text = re.sub('\{.*?\}|\[.*?\]|\=\=.*?\=\=', '', text)
    else:
        body_text =''
        
    #Preprocessing
    title_tokens=preprocess_text(title)
    infobox_tokens=preprocess_text(infobox,True)
    body_tokens=preprocess_text(body_text,True)
    category_tokens=preprocess_text(category)
    references_tokens=preprocess_text(references)
    links_tokens=preprocess_text(references)
    
    #Indexing
    unique_tokens = set(title_tokens)|set(infobox_tokens)|set(body_tokens)|set(category_tokens)|set(references_tokens)|set(links_tokens)
    for token in unique_tokens:
        token_str = str(doc_id)+'-'
        if token in title_tokens:
            token_str += 't'+str(title_tokens.count(token))
        if token in body_tokens:
            token_str += 'b'+str(body_tokens.count(token))
        if token in infobox_tokens:
            token_str += 'i'+str(infobox_tokens.count(token))
        if token in category_tokens:
            token_str += 'c'+str(category_tokens.count(token))
        if token in references_tokens:
            token_str += 'r'+str(references_tokens.count(token))
        if token in links_tokens:
            token_str += 'l'+str(links_tokens.count(token))
        
        if token not in pl:
            pl[token] = token_str
        else:
            pl[token] = pl[token] + ";" + token_str 

class XMLParser(xml.sax.ContentHandler):
    
    def __init__(self):
        self.id =''
        self.tag = ''
        self.title = ''
        self.ns=''
        self.text = ''

    def startElement(self,name,attrs):

        self.tag=name

    def endElement(self,name):
        global num_pages
        global pl
        global c
        if name=='page':
            id_title_map[num_pages]=self.title.lower().strip()
            
            # Extracting the useful info from title and text
            
            #extract_useful_info(self.id.split('\n')[0],self.title,self.text,self.ns)
            extract_useful_info(num_pages,self.title,self.text,self.ns)
            num_pages+=1
            if num_pages%10000==0:
                print(num_pages)
            
            if num_pages%100000==0:
                print('Writing Intermediate Index after {} pages'.format(num_pages))
                with open(index_path + str(num_pages)+'_index.txt','w') as fp:
                    pl=dict(OrderedDict(sorted(pl.items())))
                    for i in pl:
                        fp.write(i+':'+pl[i])
                        fp.write('\n')
                    
                with open(inverted_stat_path + str(num_pages)+'_invertedindex_stat.txt','w') as f:
                    f.write(str(c))
                    f.write('\n')
                    f.write(str(len(pl)))
                    del pl
                    pl={}
                    c=0
                

            self.id = ''
            self.tag = ''
            self.title = ''
            self.ns = ''
            self.text = ''

    def characters(self, content):
        if self.tag =='id':
            self.id += content
        if self.tag == 'title':
            self.title += content
        if self.tag =='ns':
            self.ns += content
        if self.tag == 'text':
            self.text += content
            
            
### Running the code
parser = xml.sax.make_parser()
parser.setFeature(xml.sax.handler.feature_namespaces,False)
xml_parser = XMLParser()
parser.setContentHandler(xml_parser)

# print('reading the dump')
# output=parser.parse(dump_path)

with bz2.BZ2File(dump_path) as bz_file:
   print("reading dump: \n")
   output = parser.parse(bz_file)

# writing Index File
print('Writing Intermediate Index after {} pages'.format(num_pages))
with open(index_path + str(num_pages)+'_index.txt','w') as fp:
    pl=dict(OrderedDict(sorted(pl.items())))
    for i in pl:
        fp.write(i+':'+pl[i])
        fp.write('\n')
    pl={}
with open(inverted_stat_path + str(num_pages)+'_invertedindex_stat.txt','w') as f:
    f.write(str(c))
    f.write('\n')
    f.write(str(len(pl)))
    c=0

id_index_map = ''
counter = 0
with open(index_path + "id_title_map.txt", 'w') as fp:
    for doc_id in id_title_map:
        fp.write(str(doc_id)+":"+str(id_title_map[doc_id])+"\n")
        id_index_map += str(doc_id)+"-"+str(counter)+";"
        counter += 1

id_index_map = id_index_map.rstrip(';')
with open(index_path + "id_index_map.txt", 'w') as fp:
    fp.write(id_index_map)
    
et=time.time()
print('time took for creating and writing index:',et-st)