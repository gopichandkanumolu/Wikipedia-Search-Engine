# Importing Libraries
#!pip install pystemmer
import time
st=time.time()
import re
import sys
import Stemmer
import xml.sax
from collections import defaultdict
import json
import pickle


dump_path=sys.argv[1]
index_path = sys.argv[2]
inverted_stat_path = sys.argv[3]

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

from collections import defaultdict
pl=defaultdict(lambda: defaultdict(dict))
c=0

# Creating Index

def create_index(doc_id,tokens,tag):
    for token in tokens:
        try:
            pl[token][tag][doc_id]+=1
        except:
            pl[token][tag][doc_id]=1
            
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
    
    create_index(doc_id,title_tokens,'t')
    create_index(doc_id,infobox_tokens,'i')
    create_index(doc_id,body_tokens,'b')
    create_index(doc_id,category_tokens,'c')
    create_index(doc_id,references_tokens,'r')
    create_index(doc_id,links_tokens,'l')
    
    
num_pages = 0
id_title_map = {}

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
        if name=='page':
            id_title_map[num_pages]=self.title.lower().strip()
            
            # Extracting the useful info from title and text
            
            extract_useful_info(self.id.split('\n')[0],self.title,self.text,self.ns)
            #extract_useful_info(num_pages,self.title,self.text,self.ns)
            num_pages+=1
            if num_pages%10000==0:
                print(num_pages)
                    

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
            
            
parser = xml.sax.make_parser()
parser.setFeature(xml.sax.handler.feature_namespaces,False)
xml_parser = XMLParser()
parser.setContentHandler(xml_parser)


output=parser.parse(dump_path)

# writing Index File

import pickle
with open(index_path+'/index.pkl','wb') as fp:
    pickle.dump(dict(pl),fp)
    
with open(inverted_stat_path+'/invertedindex_stat.txt','w') as f:
    f.write(str(c))
    f.write('\n')
    f.write(str(len(pl)))
    
et=time.time()
print('time took for creating and writing index:',et-st)