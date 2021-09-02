""" import libraries """
from urllib.request import urlopen
from bs4 import BeautifulSoup
import lxml
import requests
import re
import pandas as pd
import time

"""initialise a session""" 

# load the landing page
landing_page = "https://www.bbc.co.uk/programmes/b006qnmr/episodes/player?page={}"
html = requests.get(landing_page.format(1))
soup = BeautifulSoup(html.content, 'html.parser')

# now find the number of pages
npages = int(soup.find('li', {"class": "pagination__page--last"}).find('a').text)
print(f"I found {npages} pages on the website")

""" run through the pages and fetch title and url_list """ 
title_list = []
title_url_list = []

for page in range(1, npages+1):
    html = requests.get(landing_page.format(page))
    soup = BeautifulSoup(html.content, 'html.parser')
    
    for title in soup.find_all('h2', class_='programme__titles'):
        title_list.append(title.text)
        for href in title:
            title_url_list.append(href['href'])
        print("\r processing - ", "{:.2%}".format(page/npages), end='')

""" returns a dictionary of the eight discs, book choice, luxury item and favourite """

def unpack_blurb(blurb):
  return {
      'disc one': blurb[re.search("DISC ONE: ", blurb).span(0)[1] : re.search("DISC TWO: ", blurb).span(0)[0]],
      'disc two': blurb[re.search("DISC TWO: ", blurb).span(0)[1] : re.search("DISC THREE: ", blurb).span(0)[0]],
      'disc three': blurb[re.search("DISC THREE: ", blurb).span(0)[1] : re.search("DISC FOUR: ", blurb).span(0)[0]],
      'disc four': blurb[re.search("DISC FOUR: ", blurb).span(0)[1] : re.search("DISC FIVE: ", blurb).span(0)[0]],
      'disc five': blurb[re.search("DISC FIVE: ", blurb).span(0)[1] : re.search("DISC SIX: ", blurb).span(0)[0]],
      'disc six': blurb[re.search("DISC SIX: ", blurb).span(0)[1] : re.search("DISC SEVEN: ", blurb).span(0)[0]],
      'disc seven': blurb[re.search("DISC SEVEN: ", blurb).span(0)[1] : re.search("DISC EIGHT: ", blurb).span(0)[0]],
      'disc eight': blurb[re.search("DISC EIGHT: ", blurb).span(0)[1] : re.search("BOOK CHOICE: ", blurb).span(0)[0]],
      'book choice': blurb[re.search("BOOK CHOICE: ", blurb).span(0)[1] : re.search("LUXURY ITEM: ", blurb).span(0)[0]],
      'luxury item': blurb[re.search("LUXURY ITEM: ", blurb).span(0)[1] : re.search("CASTAWAY'S FAVOURITE: ", blurb).span(0)[0]],
      'favourite': blurb[re.search("CASTAWAY'S FAVOURITE: ", blurb).span(0)[1] : re.search("Presenter", blurb).span(0)[0]]
  }

  """ run through the different episodes """ 

DF = pd.DataFrame(columns = ['guest', 'artist', 'track', 'label', 'presenter', 'producer', 'book_choice', 'luxury_item', 'favourite', 'synopsis', 'url'])

for ep in range(1, len(title_url_list)+1):
    html = requests.get(title_url_list[ep-1])
    try: 
        soup = BeautifulSoup(html.content, 'html.parser')
    except ConnectionError:
        print("I am here")
        time.sleep(1)
        soup = BeautifulSoup(html.content, 'html.parser')

    # get the presenter and producer
    for entry in soup.find_all('p'):
        if 'Presenter:' in entry.text:
            try: # let's try splitting when a colon is used
              [presenter, producer] = entry.text[11:].split('Producer: ')
            # except ValueError: # let's try splitting when there is no colon
            #   [presenter, producer] = entry.text[10:].split('Producer ')
            except: print(f"couldn't split {entry.text} \n")

    # get the synopsis
    synopsis = ""
    for entry in soup.find_all(class_='synopsis-toggle__long'):
        synopsis += entry.text
    
    # get the tracks - if there is a nice 'music played' section
    if len(soup.find_all(class_='segment segment--music'))>0: 

      # get the book choice, luxury item and favourite
      for entry in soup.find_all('p'):
          if 'BOOK CHOICE' in entry.text:
              [book_choice, luxury_item, favourite] = re.split("BOOK CHOICE:|LUXURY ITEM:|LUXURY:|CASTAWAY'S FAVOURITE:|CASTAWAY'S CHOICE:|FAVOURITE TRACK", entry.text[12:])

      for segment in soup.find_all(class_='segment segment--music'):
          if segment.find(class_='artist') is not None:
            artist = segment.find(class_='artist').text
          else: artist = ""
          
          if segment.find_all(class_='no-margin') is not None:
            try: 
              track = segment.find_all(class_='no-margin')[1].find('span').text 
            except IndexError:
              track = segment.find_all(class_='no-margin')[0].find('span').text 
            except AttributeError:
              track = segment.find_all(class_='no-margin')[0].find('span').text     
                    
          else: track = ""

          try:
            label = segment.find('abbr').text
          except AttributeError:
            label = ""
          
          # now put everything in a neat DataFrame
          DF = DF.append({'guest': title_list[ep-1], 
                            'url': title_url_list[ep-1],
                            'artist': artist, 
                            'track': track, 
                            'label':label, 
                            'presenter':presenter, 
                            'producer':producer, 
                            'book_choice':book_choice, 
                            'luxury_item':luxury_item, 
                            'favourite':favourite, 
                            'synopsis':synopsis}, ignore_index=True)
         
   #when we have to grab the tracks from the text 
    else: 
      try:
        blurb = ""
        for entry in soup.find_all('p'):
          blurb += entry.text

        blurb_scrape = unpack_blurb(blurb)

        for disc in ['disc one', 'disc two', 'disc three', 'disc four', 'disc five', 'disc six', 'disc seven', 'disc eight']:
          # now put everything in a neat DataFrame
          DF = DF.append({'guest': title_list[ep-1], 
                            'url': title_url_list[ep-1],
                            'disc': blurb_scrape[disc], 
                            'presenter':presenter, 
                            'producer':producer, 
                            'book_choice':blurb_scrape['book choice'], 
                            'luxury_item':blurb_scrape['luxury item'], 
                            'favourite':blurb_scrape['favourite'], 
                            'synopsis':synopsis}, ignore_index=True)       
      except AttributeError:
        DF = DF.append({'guest': title_list[ep-1], 
                            'url': title_url_list[ep-1]}, ignore_index=True)
        # print(f"couldn't scrape {title_list[ep-1]}, link is here: {title_url_list[ep-1]}")
    # print progress

    print("\r processing - ", "{:.2%}".format(ep/len(title_url_list)))