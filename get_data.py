import re
import requests
import pandas as pd


url = "https://www.bundestag.de/blob/375658/9f9b37023e0285311adad38248c60671/18106-data.txt"

result = requests.get(url)
content = result.content

sitzung = 106
sitzung = str(sitzung) + ". Sitzung"

begin_document = re.search(sitzung, content).end()


begin_protocol = re.search(r"Beginn: (.*?) Uhr", content[begin_document::]).end()+len(content[0:begin_document])

protocol = content[begin_protocol::]


tops = [r"Tagesordnungspunkt 4", r"Tagesordnungspunkt 5", "Tagesordnungspunkt 6", "Tagesordnungspunkt 33 h"]


begin_top_4 = re.search(tops[0] + ".*?" + ":\r\n" , protocol).end()


begin_speech = re.search(r"Bartels" + ".*?" + ":\r\n", protocol[begin_top_4::]).end() + begin_top_4


def agenda_items(sitting, content, tops):
    """
    this function takes the number of the sitting,  the raw text and the previously identified "tagesordnungspunkte" (tops).
    then it finds the beginning of the document, the actual start of the protocol and the
    beginnings of the discussions for each agenda item
    """
    sitting = str(sitting) + ". Sitzung"
    begin_document = re.search(sitting, content).end()
    begin_protocol = re.search(r"Beginn: (.*?) Uhr", content[begin_document::]).end()+begin_document
    protocol = content[begin_protocol::]
    begin_tops = []
    for top in tops:
        begin_top = re.search(top + ".*?" + ":\r\n" , protocol)
        if begin_top != None:
            begin_top = re.search(top + ".*?" + ":\r\n" , protocol).end()
        begin_tops.append(begin_top)
    return begin_tops, protocol
        


  
def find_tops(content):
    """
    This finds all the agenda items
    """
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
    return tops
    
    
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

        
    return mps, first_names, last_names, full_names, party_affiliation


tops = find_tops(content)

begin_tops, protocol = agenda_items(106, content, tops)

tops_frame = pd.DataFrame({"Name":tops, "beginning": begin_tops})

tops_frame = tops_frame.dropna()

tops_frame = tops_frame.sort('beginning')
tops_frame = tops_frame.drop_duplicates(subset = 'beginning')

admin_staff = ["Norbert Lammert", "Ulla Schmidt", "Petra Pau", "Johannes Singhammer", ]
tops_frame.iloc[:,1 ] = tops_frame.iloc[:,1].astype(int)

begin_speeches = []
for i in range(0, len(tops_frame.iloc[:,1])-1):
    top_content = protocol[tops_frame.iloc[i,1]:tops_frame.iloc[(i+1),1]]
    for full_name in full_names:
        if re.search(full_name + ".*?" + ":\r\n", top_content) and full_name not in admin_staff :
            print full_name
            begin_speech = re.search(full_name + ".*?" + ":\r\n", top_content).end() + tops_frame.iloc[i,1]
            begin_speeches.append(begin_speech)
            
    