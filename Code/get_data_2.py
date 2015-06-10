# -*- coding: utf-8 -*-
"""
Created on Sun Jun  7 14:00:36 2015

@author: timkreienkamp
"""
from __future__ import unicode_literals
import re
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
import chardet
import numpy as np

def get_url_list_sittings(base_url):
    prefix = 'https://www.bundestag.de'
    url_list = []
    sitting_list = []
    result = requests.get(base_url)
    soup = bs(result.content)
    html_link_list = soup.find('ul', {'class': 'standardLinkliste'})
    html_links = html_link_list.find_all('a')
    for link in html_links:
        url_list.append(prefix+ link['href'])
        sitting = int(link.text.split(" ")[8].strip("."))
        sitting_list.append(sitting)
    url_list = url_list[::-1]
    sitting_list = sitting_list[::-1]
    return url_list, sitting_list

admin_staff = ["Präsident Dr. Norbert Lammert", "Vizepräsidentin Ulla Schmidt", "Vizepräsidentin Petra Pau", 
               "Vizepräsident Johannes Singhammer", 
               "Vizepräsidentin Edelgard Bulmahn", 
               "Vizepräsidentin Claudia Roth",
               "Vizepräsident Peter Hintz", 
               "Norbert Lammert",
               "Johannes Singhammer", 
               "Ulla Schmidt",
               "Petra Pau",
               "Edelgard Bulmahn",
               "Claudia Roth"
               ]

def get_mps():
    """
    This gets a list of elected members of parliament, given the legislative period
    """
    from bs4 import BeautifulSoup as bs
    ###initizialize lists for result sets ###
    mps = []
    full_names = []
    first_names = []
    last_names = []
    party_affiliation = []
    #######
    
    ### scrape the webpage that contains the list of elected members####
    link = "http://www.bundestag.de/bundestag/abgeordnete18/alphabet"
    response = requests.get(link)
    soup = bs(response.content)
    main_content = soup.find('div', {'class':'standardBox'})
    blocks = main_content.find_all('ul', {'class': 'standardLinkliste'})
    
    ##### iterate through the results ####
    for block in blocks:
        list_items = block.find_all('li')
        for item in list_items:
            link = item.find('div', {'class': 'linkIntern'})
            link = link.find('a')
            mp =  link.text
            mp = mp.strip('\n')
            last_name = mp.split(',')[0]
            first_name = mp.split(',')[1]
            # check if they have a phd or professor title
            if len(first_name.split('.')) == 2  and (first_name.split('.')[0] == ' Dr'):
                first_name = first_name.split('.')[1]
                
            elif len(first_name.split('.')) == 3 and first_name.split('.')[0] == ' Prof':
                first_name = first_name.split('.')[2]
            
            # strip the cities that differentiate some mps with the same last names 
            #(we don't need those since we keep track of first names and party)
            
            if len(last_name.split('(')) > 1:
                last_name = last_name.split('(')[0]
            
            #there is a space at the beginning of every last name, let's get rid of it
            last_name = last_name[1::]
            first_name = first_name[1::]
            
            full_name = first_name + last_name
            full_name = full_name.strip()
            party = mp.split(',')[2]
            #keep raw for debugging
            mps.append(mp)
            last_names.append(last_name)
            first_names.append(first_name)
            full_names.append(full_name)
            party_affiliation.append(party)
            mps_frame = pd.DataFrame({'first_name': first_names, "last_name": last_names, 'full_name': full_names, "party": party_affiliation})
        
    return mps_frame



def get_content(sitting, url ):
    
    result = requests.get(url)
    
    
    content = result.content
    encoding = chardet.detect(content)['encoding']
    if encoding != "UTF-8-SIG":
        content = content.decode("ISO-8859-2")
    else:
        content = content.decode("UTF-8-SIG")
    #### in this block the document block before the protocol is searched for the agenda items
    ### top = German abbreviation for "TagesOrdnungsPunkt" == agenda item
    sitting = str(sitting) + ". Sitzung"
    
    begin_document = re.search(sitting, content).end()
    begin_protocol = re.search(r"Beginn: (.*?) Uhr", content[begin_document::]).end()+begin_document
    index = content[begin_document:begin_protocol]
    
    #### now we look for the beginning of the document and protocol   
    
    if re.search(r"Schluss: (.*?) Uhr", content[begin_document::]) != None:
        end_protocol = re.search(r"Schluss: (.*?) Uhr", content[begin_document::]).start()+begin_document
    elif re.search(r"Sitzung ist geschlossen", content[begin_document::]) != None:
        end_protocol = re.search(r"Sitzung ist geschlossen", content[begin_document::]).start()+begin_document
    elif re.search(r"Anlagen zum Stenografischen Bericht", content[begin_document::]) != None:
        end_protocol = re.search(r"Anlagen zum Stenografischen Bericht", content[begin_document::]).start()+begin_document
    else:
        end_protocol = len(content)-1
    protocol = content[begin_protocol:end_protocol]
    
    
    return protocol, index



def get_speaker_list(index,mps_frame):
    names = []
    index_lines = index.split('\n')
    for line in index_lines:
        line = line.split('(')
        
        if len(line) > 1:
            name = line[0]
            #encoding = chardet.detect(name)['encoding']
            #name = name.decode(encoding)
            
            
            if len(name.split(".")) == 2:
                name = name.split(".")[1]
            elif len(name.split(".")) == 3:
                name = name.split(".")[2]
            name = name.strip()
            
            if name in mps_frame.full_name.tolist():
                name = name.split(")")[0]
                names.append(name)
                #print name
            
                
            
    return names

def find_beginnings(speakers, protocol, mps_frame):
    beginning = 0
    speakers_ = []
    beginnings = []
    parties = []
    for speaker in speakers:
        party = mps_frame[mps_frame["full_name"] == speaker].party.iloc[0]
        
        if re.search(speaker + ".*?" + ":\r\n", protocol[beginning::]):
            beginning = re.search(speaker + ".*?" + ":\r\n", protocol[beginning::]).end() + beginning
            beginnings.append(beginning)
            speakers_.append(speaker)
            parties.append(party)
    speakers_beginnings = pd.DataFrame({"speaker":speakers_, "beginning":beginnings, "party":parties})
    
    return speakers_beginnings
    
def find_speeches(speakers_beginnings, admin_staff, protocol, sitting):
    speeches = []
    speakers = []
    parties = []
    
    
    for i in range(0, speakers_beginnings.shape[0]):
        speaker = speakers_beginnings.speaker[i]
        if speaker in admin_staff:
            break
        speech = ""
        start = speakers_beginnings.beginning[i]
        if i == speakers_beginnings.shape[0]-1:
            stop = len(protocol)-1
        else:
            stop = speakers_beginnings.beginning[i+1]
        snippet = protocol[start:stop]
        
        
        party = speakers_beginnings.party.iloc[i]
        paragraphs_raw = re.split(r'\r\n', snippet)
        paragraphs = []
        for i in range(0, len(paragraphs_raw)):
            if len(paragraphs_raw[i]) > 7:
                paragraphs_raw[i] = paragraphs_raw[i].strip()
                paragraphs.append(paragraphs_raw[i])
        if len(paragraphs) > 3:
            k = 3
        elif len(paragraphs) > 2:
            k = 2
        else:
            k = 1
        for i in range(0, len(paragraphs)-k):
            terminal_condition = False
            append_paragraph = False 
            for admin in admin_staff:
                
                if  re.search(admin, paragraphs[i][0:(min(60, len(paragraphs[i])))]) != None and re.match(".*?" + speaker, paragraphs[i+1]) == None and re.match(".*?" + speaker, paragraphs[i+k-1]) == None and re.match(".*?" + speaker, paragraphs[i+k]) == None:
                    terminal_condition = True
                    break
                elif re.search(admin, paragraphs[i][0:(min(60, len(paragraphs[i])))]) != None and i == len(paragraphs)-k:
                    terminal_condition = True
                    break
                elif re.match(admin, paragraphs[i]) and re.match(".*?" + speaker, paragraphs[i+1]) != None:
                    break
                elif re.match(admin, paragraphs[i]) == None and paragraphs[i][0:2] != " ("  and paragraphs[i][0] != "(":
                    append_paragraph = True
                else:
                    append_paragraph = False
                    break
            if terminal_condition == False and append_paragraph == True:
                speech = speech + " " + paragraphs[i]
            elif terminal_condition == True :
                break
        
        speeches.append(speech)
        speakers.append(speaker)
        parties.append(party)
    
    sitting_list = np.repeat([sitting], len(speeches)).tolist()
    speech_data = pd.DataFrame({'speaker':speakers, 'party':parties, 'speech':speeches, 'sitting':sitting_list})
    
    return speeches, speech_data

    
base_url = "https://www.bundestag.de/plenarprotokolle"
urls, sittings = get_url_list_sittings(base_url)

sitting = 2
url = urls[1]

mps_frame = get_mps()

protocol, index = get_content(sitting, url)

speakers_list = get_speaker_list(index,mps_frame)

speakers_beginnings = find_beginnings(speakers_list, protocol, mps_frame)

speeches, speech_data = find_speeches(speakers_beginnings, admin_staff, protocol, sitting)



output = speech_data


for i in range(2, len(sittings)):
        sitting = sittings[i]
        url = urls[i]
        print sitting
    
        protocol, index = get_content(sitting, url)
        speakers_list = get_speaker_list(index,mps_frame)
        speakers_beginnings = find_beginnings(speakers_list, protocol, mps_frame)
        

        speeches, speech_data = find_speeches(speakers_beginnings, admin_staff, protocol, sitting)
       
        output = pd.concat([output, speech_data])

output.to_csv("/users/timkreienkamp/documents/studium/data_science/tm_project/textminingproject/data/speech_data.csv", index = False)