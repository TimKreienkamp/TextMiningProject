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

def get_text_and_agenda_items(sitting, url ):
    
    result = requests.get(url)
    #result.encoding = 'UTF-8'
    
    content = result.content
    encoding = chardet.detect(content)['encoding']
    if encoding != 'utf-8':
        content = content.decode(encoding).encode('utf8')
        
    #### in this block the entire content is searched for the agenda items
    ### top = German abbreviation for "TagesOrdnungsPunkt" == agenda item
    
    tops = re.findall(r"Tagesordnungspunkt " + "[0-9]\s", content)
    tops.extend(re.findall(r"Tagesordnungspunkt " + "[0-9][0-9]\s", content))
    tops.extend(re.findall(r"Tagesordnungspunkt " + "[0-9][0-9]" + " " + "[a-z]\s" , content))
    tops.extend(re.findall(r"Tagesordnungspunkt " + "[0-9]" + " " + "[a-z]\s" , content))
    tops.extend(re.findall(r"Tagesordnungspunkt " + "[0-9]" + " " + "[a-z]:" , content))
    tops.extend(re.findall(r"Tagesordnungspunkt " + "[0-9][0-9]" + " " + "[a-z]:" , content))
    tops.extend(re.findall(r"Tagesordnungspunkt " + "[0-9]" + " " + "[a-z]:" , content))
    tops.extend(re.findall(r"Tagesordnungspunkt " + "[0-9][0-9]" + " " + "[a-z]:" , content))
    tops.extend(re.findall(r"Tagesordnungspunkt " + "[0-9]:" , content))
    tops = set(tops)
    tops = list(tops)
    for i in range(0, len(tops)):
        tops[i] = tops[i][:-1]
        
    #### now we look for the beginning of the document and protocol   
    sitting = str(sitting) + ". Sitzung"
    begin_document = re.search(sitting, content).end()
    begin_protocol = re.search(r"Beginn: (.*?) Uhr", content[begin_document::]).end()+begin_document
    if re.search(r"Schluss: (.*?) Uhr", content[begin_document::]) != None:
        end_protocol = re.search(r"Schluss: (.*?) Uhr", content[begin_document::]).start()+begin_document
    elif re.search(r"Sitzung ist geschlossen", content[begin_document::]) != None:
        end_protocol = re.search(r"Sitzung ist geschlossen", content[begin_document::]).start()+begin_document
    elif re.search(r"Anlagen zum Stenografischen Bericht", content[begin_document::]) != None:
        end_protocol = re.search(r"Anlagen zum Stenografischen Bericht", content[begin_document::]).start()+begin_document
    else:
        end_protocol = len(content)-1
    protocol = content[begin_protocol:end_protocol]
    begin_tops = []
    ### now we look for the beginning of the discussion for each top
    for top in tops:
        begin_top = re.search(top + ".*?" + ":\r\n" , protocol)
        if begin_top != None:
            begin_top = re.search(top + ".*?" + ":\r\n" , protocol).end()
        begin_tops.append(begin_top)
    
    #finally collect everything in a dataframe and sort
    tops_frame = pd.DataFrame({"Name":tops, "beginning": begin_tops})
    tops_frame = tops_frame.dropna()
    tops_frame = tops_frame.sort('beginning')
    tops_frame = tops_frame.drop_duplicates(subset = 'beginning')
    tops_frame.iloc[:,1] = tops_frame.iloc[:,1].astype(int)
    # return the actual protocol and the dataframe with the beginning of the tops
    return tops_frame, protocol


def find_beginnings(tops_frame, mps_frame):
    """ 
    this function takes the dataframe with the beginning of each agenda item and the frame with all MP's 
    and finds the beginning of every speech
    """
    
    begin_speeches = []
    speakers = []
    parties = []
    for i in range(0, len(tops_frame.iloc[:,1])):
        if i != len(tops_frame.iloc[:,1])-1:
            top_content = protocol[tops_frame.iloc[i,1]:tops_frame.iloc[(i+1),1]]
        else:
            top_content = protocol[tops_frame.iloc[i,1]::]
        for j in range(0, mps_frame.shape[0]):
            full_name = mps_frame.iloc[j,1]
            party = mps_frame.iloc[j,3]
            if re.search(full_name + ".*?" + ":\r\n", top_content) and full_name not in admin_staff :
                begin_speech = re.search(full_name + ".*?" + ":\r\n", top_content).end() + tops_frame.iloc[i,1]
                begin_speeches.append(begin_speech)
                speakers.append(full_name)
                parties.append(party)
    begin_speeches_mps = pd.DataFrame({'speaker':speakers, 'beginning':begin_speeches, 'party':parties})
    begin_speeches_mps = begin_speeches_mps.sort('beginning')
    return begin_speeches_mps
            
                        
        


    
    
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
            party = mp.split(',')[2]
            #keep raw for debugging
            mps.append(mp)
            last_names.append(last_name)
            first_names.append(first_name)
            full_names.append(full_name)
            party_affiliation.append(party)
            mps_frame = pd.DataFrame({'first_name': first_names, "last_name": last_names, 'full_name': full_names, "party": party_affiliation})
        
    return mps_frame


def find_speeches(begin_speeches_mps, admin_staff, protocol, sitting):
    speeches = []
    speakers = []
    parties = []
    for i in range(0, begin_speeches_mps.shape[0]-1):
        speech = ""
        snippet = protocol[begin_speeches_mps.iloc[i,0]:begin_speeches_mps.iloc[i+1,0]]
        speaker = begin_speeches_mps[["speaker"]].iloc[i,0]
        if speaker in admin_staff:
            break
        party = begin_speeches_mps[["party"]].iloc[i,0]
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
                if  re.match(admin, paragraphs[i]) != None and re.match(".*?" + speaker, paragraphs[i+1]) == None and re.match(".*?" + speaker, paragraphs[i+k-1]) == None and re.match(".*?" + speaker, paragraphs[i+3]) == None:
                    terminal_condition = True
                    break
                elif re.match(admin, paragraphs[i]) and i == len(paragraphs)-k:
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
                speech = speech + paragraphs[i]
            elif terminal_condition == True :
                break
        
        speeches.append(speech)
        speakers.append(speaker)
        parties.append(party)
    
    sitting_list = np.repeat([sitting], len(speeches)).tolist()
    speech_data = pd.DataFrame({'speaker':speakers, 'party':parties, 'speech':speeches, 'sitting':sitting_list})
    
    return speeches, speech_data

admin_staff = ["Präsident Dr. Norbert Lammert", "Vizepräsidentin Ulla Schmidt", "Vizepräsidentin Petra Pau", 
               "Vizepräsident Johannes Singhammer", 
               "Vizepräsidentin Edelgard Bulmahn", 
               "Vizepräsidentin Claudia Roth",
               #"Pr\xe4sident Dr. Norbert Lammert",
               #"Vizepr\xe4sidentin Ulla Schmidt", 
                #"Vizepr\xe4sidentin Petra Pau", 
                #"Vizepr\xe4sident Johannes Singhammer", 
                #"Vizepr\xe4sidentin Edelgard Bulmahn",
                #"Vizepr\xe4sidentin Claudia Roth"
             ]  

for admin in admin_staff:
    admin.encode('UTF-8')

sitting = 2
url = urls[1]

mps_frame = get_mps()

tops_frame, protocol = get_text_and_agenda_items(sitting, url)
        
begin_speeches_mps = find_beginnings(tops_frame, mps_frame)

speeches, speech_data = find_speeches(begin_speeches_mps, admin_staff, protocol, sitting)

base_url = "https://www.bundestag.de/plenarprotokolle"
urls, sittings = get_url_list_sittings(base_url)

output = speech_data


for i in range(1, len(sittings)):
        sitting = sittings[i]
        url = urls[i]
        print sitting
    
        tops_frame, protocol = get_text_and_agenda_items(sitting, url)
        
        begin_speeches_mps = find_beginnings(tops_frame, mps_frame)

        speeches, speech_data = find_speeches(begin_speeches_mps, admin_staff, protocol, sitting)
        output = pd.concat([output, speech_data])
        