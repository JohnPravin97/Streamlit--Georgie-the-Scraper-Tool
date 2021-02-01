import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request, urlretrieve
from IPython.display import IFrame, display
from PIL import Image
from selenium import webdriver
import os
import streamlit as st

def relevant_book_scraper(inp):
    url = 'https://www.google.com//search?tbm=bks&q='+ inp
    driver = webdriver.Chrome(executable_path=r'C:\Users\jpravijo\Desktop\Anaconda\chromedriver_win32 (3)\chromedriver.exe')
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html,'lxml')
    driver.close()
    book_name_list, authors_list, relevant_no_list, links_list = [], [], [], []
    k = 1
    for i, content in enumerate(soup.find_all('div', class_='bHexk Tz5Hvf')):
        if k>5:
            break
        
        # Book Names Scraping
        try:
            book_name = content.find('h3', class_='LC20lb DKV0Md').text
            book_name = book_name.split('-')[0]
        except:
            book_name = 'Book Name not found'
        
        # Authors Names Scraping
        try:
            authors = content.find('div', class_='N96wpd').text
            authors = authors.split('·')[0]
        except:
            authors = ' Authors Name not found'
        
        # Detailed Information links Scraping
        try:
            try:
                links = content.find('a', class_='yKioRe VZ2GVc')['href']
            
            except:
                links = content.find('a')['href']
                
            if 'edition' in links:
                links = 'https://www.google.co.in' + links

        except:
            links = 'Links Not Found'   
        
        if book_name not in book_name_list:
            book_name_list.append(book_name)
            authors_list.append(authors)
            relevant_no_list.append(k)
            links_list.append(links)
            k+=1
        
        else:
            continue
        
    dic = {'Relevant_No': relevant_no_list, 'Books_Name' : book_name_list, 'Author_Names':authors_list, 'Links':links_list}
    df = pd.DataFrame(dic)
    df.set_index('Relevant_No', inplace=True)

    return df

inp = st.text_input('Enter the topic to get top relevant books :') 

if inp != " ":
    df = relevant_book_scraper(inp)
    
st.dataframe(df)

def book_details(df, index):
    index-=1
    url = df.iloc[index, 2]
    book_name = df.iloc[index, 0]
    driver = webdriver.Chrome(executable_path=r'C:\Users\jpravijo\Desktop\Anaconda\chromedriver_win32 (3)\chromedriver.exe')
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html,'lxml')
    driver.close()
    st.write(f'THE DETAILS ARE AS FOLLOWS')
    st.write(f'Book Name: {book_name} ')
    
    # Title page image scraping
    filepath = r"C:\Users\jpravijo\Desktop\Anaconda\Book Images\\" + book_name + ".png"
    try:
        try:
            name = soup.find('div', class_="WnWrFd").text
            img = soup.find('img', alt=name)['src']
        except:
            img = soup.find('img', class_='rISBZc M4dUYb')['src']
        urlretrieve(img, filepath)
        image = Image.open(filepath)
    except:
        image='Not Found'
    
    # To Scrape and Print the Details
    for i, content in enumerate(soup.find_all('div', class_="Z1hOCe")):
        st.write(content.text)
    return image

index = int(st.text_input('enter the index of the favourate book from above for more details:'))

if index !=0:
    image = book_details(df, index)
    st.image(image)