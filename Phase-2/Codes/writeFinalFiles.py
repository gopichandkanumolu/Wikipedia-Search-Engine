#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Importing Libraries
import time
import os
from tqdm import tqdm
import pickle


# In[2]:


source_dir = "./Final/index_files/"
dest_dir = "./final_files/"
titles_dir = "./Final/maps/"


# In[3]:


list_of_input_files = [source_dir + file_name for file_name in os.listdir(source_dir)]
print(len(list_of_input_files))
print(list_of_input_files[:5])


# In[4]:


list_of_file_names = [chr(i) for i in range(ord('a'), ord('z')+1)]
list_of_file_names.extend([chr(i) for i in range(ord('0'), ord('9')+1)])
print(list_of_file_names)


# In[5]:


files_per_char = 50
files_per_tilte = 150


# ### Secondary index files for titles

# In[20]:


input_file_path = titles_dir + "id_title_map.txt"

titles_data = {}
with open(input_file_path, 'r') as fp:
    for line in tqdm(fp.readlines()):
        line = line.strip()
        index, title = line.split(':', 1)
        index = int(index.strip())
        title = title.strip()
        titles_data[index] = title

print("Sorting the postings dictionary by keys")
titles_data = dict(sorted(titles_data.items()))

lines = len(titles_data)
title_start_end_map = ''
sub_entries_per_file = int(lines/files_per_tilte)
print("#tokens: ", lines)
print("#Sub-files: ", sub_entries_per_file)
print("Files per title: ", files_per_tilte)
start_line = 0
end_line = 0
counter = 0
file_counter = 0

print("Generating secondary index files")
write_data = []
for token in titles_data:
    write_data.append(str(token)+":"+titles_data[token].strip())
    counter += 1
    if(counter%sub_entries_per_file==0):        
        start_line = end_line
        end_line = start_line + sub_entries_per_file
        if(file_counter==files_per_tilte-1):
            end_line = lines
        file_counter += 1
        
        with open(dest_dir + "title_" + str(file_counter)+".txt", 'w') as fp:
            fp.write("\n".join([line.strip() for line in write_data]))
        
        start_token = write_data[0].strip().split(':')[0].strip()
        end_token = write_data[-1].strip().split(':')[0].strip()
        title_start_end_map += str(start_token + "_" + end_token + "=" + str(file_counter)) + '\n'
        write_data = []

with open(dest_dir + "title_info.txt", 'w') as fp:
    fp.write(title_start_end_map)

del titles_data


# ### Secondary index files for each token starting letter

# In[6]:


for char in list_of_file_names:
    output_file_path = dest_dir + char+".txt"
    print("Processing: ", output_file_path, " and merging positngs of tokens startswith '", char, "'")
    
    postings_data = {}
    for input_file_path in tqdm(list_of_input_files):
        with open(input_file_path, 'r') as fp:
            for line in fp.readlines():
                line = line.strip()
                token, postings = line.split(':', 1)
                start_letter = token[0]
                if start_letter == char:
                    if token in postings_data:
                        postings_data[token] += ";"+postings
                    else:
                        postings_data[token] = postings
                elif start_letter > char:
                    break
    
    print("Sorting the postings dictionary by keys")
    postings_data = dict(sorted(postings_data.items()))

    lines = len(postings_data)
    token_start_end_map = ''
    sub_entries_per_file = int(lines/files_per_char)
    print("#tokens: ", lines)
    print("#Sub-files: ", sub_entries_per_file)
    start_line = 0
    end_line = 0
    counter = 0
    file_counter = 0

    print("Generating secondary index files")
    write_data = []
    for token in tqdm(postings_data):
        write_data.append(token+":"+postings_data[token].strip())
        counter += 1
        if(counter%sub_entries_per_file==0):        
            start_line = end_line
            end_line = start_line + sub_entries_per_file
            if(file_counter==files_per_char-1):
                end_line = lines
            file_counter += 1
            
            with open(dest_dir + char + "_" + str(file_counter)+".txt", 'w') as fp:
                fp.write("\n".join([line.strip() for line in write_data]))
            
            start_token = write_data[0].strip().split(':')[0].strip()
            end_token = write_data[-1].strip().split(':')[0].strip()
            token_start_end_map += str(start_token + "_" + end_token + "=" + str(file_counter)) + '\n'
            write_data = []

    with open(dest_dir + char + "_info.txt", 'w') as fp:
        fp.write(token_start_end_map)
    
    del postings_data

