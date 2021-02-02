import pandas as pd
from bs4 import BeautifulSoup
from urllib.request import urlopen, Request, urlretrieve
from IPython.display import IFrame, display
from PIL import Image
from selenium import webdriver
import os
import streamlit as st
from webdriver_manager.chrome import ChromeDriverManager
try:
    import streamlit.ReportThread as ReportThread
    from streamlit.server.Server import Server
except Exception:
    # Streamlit >= 0.65.0
    import streamlit.report_thread as ReportThread
    from streamlit.server.server import Server


class SessionState(object):
    def __init__(self, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)


    def get(**kwargs):
    
        # Hack to get the session object from Streamlit.
    
        ctx = ReportThread.get_report_ctx()
    
        this_session = None
    
        current_server = Server.get_current()
        if hasattr(current_server, '_session_infos'):
            # Streamlit < 0.56
            session_infos = Server.get_current()._session_infos.values()
        else:
            session_infos = Server.get_current()._session_info_by_id.values()
    
        for session_info in session_infos:
            s = session_info.session
            if (
                # Streamlit < 0.54.0
                (hasattr(s, '_main_dg') and s._main_dg == ctx.main_dg)
                or
                # Streamlit >= 0.54.0
                (not hasattr(s, '_main_dg') and s.enqueue == ctx.enqueue)
                or
                # Streamlit >= 0.65.2
                (not hasattr(s, '_main_dg') and s._uploaded_file_mgr == ctx.uploaded_file_mgr)
            ):
                this_session = s
    
        if this_session is None:
            raise RuntimeError(
                "Oh noes. Couldn't get your Streamlit Session object. "
                'Are you doing something fancy with threads?')
    
        # Got the session object! Now let's attach some state into it.
    
        if not hasattr(this_session, '_custom_session_state'):
            this_session._custom_session_state = SessionState(**kwargs)
    
        return this_session._custom_session_state

#Youtube Scraper Functions
@st.cache(suppress_st_warning=False) 
def youtube_scraper(inp):
    
    Search = '+'.join(inp.split())
    
    driver = webdriver.Chrome(executable_path='chromedriver.exe')
    driver.get('https://www.youtube.com/results?search_query='+Search)
    html = driver.page_source
    soup = BeautifulSoup(html)
    search = soup.find('body', dir='ltr')
    first_content = soup.find('div', id='content')
        
    index_list, link,name,channel=[],[],[],[]
    
    for i,second_content in enumerate (first_content.find_all('div', class_='text-wrapper style-scope ytd-video-renderer')):
        try:
            third_content=second_content.find('h3', class_='title-and-badge style-scope ytd-video-renderer')

            # To get the link of the song
            link.append(('https://www.youtube.com'+(third_content.a)['href']).strip())


            # To get the name of the song
            k=third_content.a.text.strip()
            name.append(k)

            # To get the channel details of the songs
            channel.append(second_content.find('div', class_='hidden style-scope paper-tooltip').text.strip())
            
            index_list.append(i+1)
            
            if i>10:
                break

        except:
            pass
    dic={'Top Searches':index_list, 'Name of the Songs': name, 'Channel': channel, 'Links':link}   
    driver.close()
    df = pd.DataFrame(dic)
    df = df.iloc[:5,:]
    df.set_index(keys='Top Searches', inplace=True)
    return df

#Book Scraper Functions
@st.cache(suppress_st_warning=False)
def relevant_book_scraper(inp):
    url = 'https://www.google.com//search?tbm=bks&q='+ inp
    driver = webdriver.Chrome(executable_path='chromedriver.exe')
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
@st.cache(suppress_st_warning=False)
def book_details(df, index):
    index-=1
    url = df.iloc[index, 2]
    book_name = df.iloc[index, 0]
    driver = webdriver.Chrome(executable_path='chromedriver.exe')
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html,'lxml')
    driver.close()
    content_list = []
    
    # Title page image scraping
    filepath = r"\Book Images\\" + book_name + ".png"
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
        content_list.append(content.text)
    return image, content_list

#Celebrity Scraper Functions
@st.cache(suppress_st_warning=False)
def spelling_checker(x):
    crt_inp=''
    search = '+'.join(x.split())
    url='https://www.google.com/search?q='+ search
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(url)
    html = driver.page_source
    soup = BeautifulSoup(html,'lxml')
    driver.close()
    try:
        first = soup.find('div', id='taw')
        crt_inp=first.find('a', class_='gL9Hy').text
    except:
        crt_inp=x
    return crt_inp
@st.cache(suppress_st_warning=False)
def process_inp(x):
    temp=''
    for i in x.split():
        temp = temp + ' '+ i.capitalize()
    name = temp.lstrip()
    temp = '_'.join(name.split())
    return temp, name
@st.cache(suppress_st_warning=False)
def celebrity_func(inp, name):
    url='https://en.wikipedia.org/wiki/'+inp
    html=urlopen(url)
    soup=BeautifulSoup(html,'lxml')
    first = soup.find('div', id='mw-content-text')
    try:
        Description = first.find('div', class_='shortdescription nomobile noexcerpt noprint searchaux').text
    except:
        Description = 'Not Found'
    try:
        DOB = first.find('span', class_='bday').text
    except:
        DOB = 'Not Found'
    try:
        image_link = "https:" + first.find('a', class_='image').img['src']
    except:
        image_link = 'Not Found'
    
    #Birth_Place = first.find('span', class_='birthplace').text
    #Birth_Place = first.find('td', class_='birthplace').text
    #Birth_Place = first.find('div', class_='birthplace').text
    for y in ['div', 'span', 'td']: 
        try:
            Birth_Place = first.find(y, class_='birthplace').text
            Birth_Place = ' '.join(Birth_Place.split('\n'))
            Birth_Place = ' '.join(Birth_Place.split(' '))
            Birth_Place = ''.join(Birth_Place.split('[')[0])
            break
        except:
            Birth_Place = ''
    dic={'Name': name, 'Description': Description, 'DOB': DOB, 'Birth_Place':Birth_Place, 'Image_Link':image_link, 'URL':url}
    return dic

st.set_page_config(layout="wide")


lis = ('Tutorials', 'Scraper Sections', 'Exit' )
dic = {'Tutorials': ' ', 'Scraper Sections': ['Youtube Scraper', 'Book Scraper', 'Celebrity Scraper'], 'Exit': 'Exit'}
picks = st.sidebar.selectbox('Please Choose From the below', lis)

if picks =='Tutorials':
    '''
    # Welcome!! "Georgie the Scraper" is here to help you 
    '''
    
    ''' Please expand each scrapers tab for their functionalities and implementations '''
    ys = st.beta_expander('Youtube Scraper', expanded=False)
    with ys:
        st.markdown('<p style="color:blue"><b> Youtube Scraper has the following functionalities built inside it:</b> </p>', unsafe_allow_html=True)
        st.markdown('<ul style="list-style-type:disc"> 1. Extracts the user-defined video from YouTube. </ul>', unsafe_allow_html=True)
        st.markdown('<ul style="list-style-type:disc"> 2. Plays the extracted video for the user. </ul>', unsafe_allow_html=True)
        st.markdown(' ')    
        
        st.markdown('<p style="color:blue"><b> The steps to follow along with Youtube Scraper</b> </p>', unsafe_allow_html=True)
        
        columns = st.beta_columns(2)
        columns[0].markdown('<ul style="list-style-type:disc"> <b> 1. To navigate to the Youtube Scraper </b></u>', unsafe_allow_html=True)
        columns[0].markdown('<ul style="list-style-type:disc">  (i) Go to Sidebar window \
                            <br>(ii) Select Scraper Sections </br> \
                    (iii) Click Youtube Scraper \
                    <br> Then you are in Youtube Scraper </br></ul>', unsafe_allow_html=True)
      
        columns[1].markdown('<ul style="list-style-type:disc"> <b> 2.  To watch a song </b></u>', unsafe_allow_html=True)
        columns[1].markdown('<ul style="list-style-type:disc"> (i) Type the song name and press Enter\
                            <br> (ii) Click Search button </br></ul>', unsafe_allow_html=True)    
        columns[1].markdown('<ul style="list-style-type:disc"> \
                    (iii) Choose the songs by the index form dataframe\
                    <br>(iv) Click Another Video button for another songs from the dataframe </br>\
                    (v) Repeat step (iii) \
                    <br>(vi) Remove the text from the text input and press enter to close </br></ul>', unsafe_allow_html=True)
                    
           
            
            
    bs = st.beta_expander('Book Scraper', expanded=False)
    with bs:
        st.markdown('<p style="color:blue"><b> Book Scraper has the following functionalities built inside it:</b> </p>', unsafe_allow_html=True)
        st.markdown('<ul style="list-style-type:disc"> 1. Returns the top (five) books that align with user search input. </ul>', unsafe_allow_html=True)
        st.markdown('<ul style="list-style-type:disc"> 2. Upon user request can provide more details about the book the user is looking for.</ul>', unsafe_allow_html=True)
        st.markdown(' ')
        
        st.markdown('<p style="color:blue"><b> The steps to follow along with Book Scraper</b> </p>', unsafe_allow_html=True)
        
        columns = st.beta_columns(2)
        columns[0].markdown('<ul style="list-style-type:disc"> <b> 1. To navigate to the Book Scraper </b></u>', unsafe_allow_html=True)
        columns[0].markdown('<ul style="list-style-type:disc">  (i) Go to Sidebar window \
                            <br>(ii) Select Scraper Sections </br> \
                    (iii) Click Book Scraper \
                    <br> Then you are in Book Scraper </br></ul>', unsafe_allow_html=True)
      
        columns[1].markdown('<ul style="list-style-type:disc"> <b> 2.  To Search for the relevant books </b></u>', unsafe_allow_html=True)
        columns[1].markdown('<ul style="list-style-type:disc"> (i) Type the book/topic name and press Enter\
                            <br> (ii) Click Search button </br></ul>', unsafe_allow_html=True)    
        columns[1].markdown('<ul style="list-style-type:disc"> \
                    (iii) Choose the books by the index form dataframe\
                    <br>(iv) Click Another Video button to close the details page </br>\
                    (v) To select another book -> Repeat step (iii) \
                    <br>(vi) Remove the text from the text input and press enter to close </br></ul>', unsafe_allow_html=True)
                    
                    
                        
    cs = st.beta_expander('Celebrity Scraper', expanded=False)
    with cs:
        st.markdown('<p style="color:blue"><b> Celebrity Scraper has the following functionalities built inside it: </b> </p>', unsafe_allow_html=True)
        st.markdown('<ul style="list-style-type:disc"> 1. Spell checks user input and outputs the correct spelling if the user input does not match with the database.</ul>', unsafe_allow_html=True)
        st.markdown('<ul style="list-style-type:disc"> 2. Provides the user with the celebrity information and upon request.</ul>', unsafe_allow_html=True)
        
        st.markdown(' ')
        
        st.markdown('<p style="color:blue"><b> The steps to follow along with Celebrity Scraper</b> </p>', unsafe_allow_html=True)
        
        columns = st.beta_columns(2)
        columns[0].markdown('<ul style="list-style-type:disc"> <b> 1. To navigate to the Celebrity Scraper </b></u>', unsafe_allow_html=True)
        columns[0].markdown('<ul style="list-style-type:disc">  (i) Go to Sidebar window \
                            <br>(ii) Select Scraper Sections </br> \
                    (iii) Click Celebrity Scraper \
                    <br> Then you are in Celebrity Scraper </br></ul>', unsafe_allow_html=True)
                    
        columns[1].markdown('<ul style="list-style-type:disc"> <b> 2.  To Search the details of a celebrity </b></u>', unsafe_allow_html=True)
        columns[1].markdown('<ul style="list-style-type:disc"> (i) Type the celebrity name and press Enter\
                            <br> (ii) Click Search button </br></ul>', unsafe_allow_html=True)    
        columns[1].markdown('<ul style="list-style-type:disc"> \
                    (iii) Click yes button, if the shown image is correct, else step (iv) \
                    <br>(iv) Click no button </br>\
                    (v) Remove the text from the text input and press enter to close </ul>', unsafe_allow_html=True)
    
elif picks=='Exit':
    
    st.header('Hi There!!! You are Exited. Come Back Soon')
    
else:
    '''
    # Welcome!! "Georgie the Scraper" is here to help you 
    '''
    option = st.sidebar.radio('Which Scraper to launch', dic[picks] )

    if option == 'Book Scraper':
        
        
        '''
        ## **Book Scraper**
        '''

        text=st.empty()
        inp = text.text_input("Enter the topic to get top relevant books :")
        state = SessionState.get(flag=False)
        if (not inp):
            st.write('Please enter the book/topic name to get the search button')
            state.flag=False
        
        else:        
            if (st.button('Search') or state.flag ==True):
                spell_inp = spelling_checker(inp)
                spell_inp, _ = process_inp(spell_inp)
                checker = '/'+ spell_inp
                books_save = pd.HDFStore('bookscraper.h5')  
                if checker in books_save.keys():
                     df = books_save.get(checker)
                else:
                    df = relevant_book_scraper(inp)
                    books_save.put(spell_inp, df, data_columns=True)

                st.dataframe(df, width=10000, height=10000)
                state.flag = True
                books_save.close()
                index = st.number_input('Enter the index of the favourate book from above for more details:', min_value=0, max_value=5, step=1)
                                
                if index != 0:
                    st.write('You have chosen this book " ' + df.iloc[index-1, 0] +'" for more details')
                
                cols = st.beta_columns(5)
                button_number = cols[0].button('Go On')
                if button_number and index !=0:
                    book = cols[2].button('Another book')
                    book_name = df.iloc[index-1, 0]
                    image, content_list = book_details(df, index)
                    st.write(f'THE DETAILS ARE AS FOLLOWS')
                    st.write(f'Book Name: {book_name} ')
                    for content in content_list:
                        st.markdown(content)
                    try:
                        st.image(image)
                    except:
                        st.write('Image Not Available')
                    if book:
                        state.flag = False

  
    
    elif option == 'Youtube Scraper':
        '''
        ## **Youtube Scraper**
    
        '''
        text=st.empty()
        inp = text.text_input("Enter the song to play from youtube")
        state = SessionState.get(flag=False)
        if (not inp):
            st.write('Please enter the song name to get the search button')
            state.flag=False
        
        else:        
            if (st.button('Search') or state.flag ==True):
                st.write('Please wait - John is scraping the information needed')
                df = youtube_scraper(inp)
                st.dataframe(df, width=10000, height=10000)
 
                index = st.number_input('Enter the index of the to play the song:', min_value=0, max_value=5, step=1)
                state.flag = True
                if index != 0:
                    st.write('You have chosen to play ->' + df.iloc[index-1, 0] + ' -> Press Go On to continue')
                cols = st.beta_columns(5)
                button_number = cols[0].button('Go On')
                if button_number and index !=0:
                    st.video(df.iloc[index-1, 2])
                    finish = cols[2].button('Another video')
                    if finish:
                        state.flag = False


 
    elif option =='Celebrity Scraper':
        
        '''
        ## **Celebrity Scraper**
        '''
        text=st.empty()
        spell_inp = text.text_input("Enter the celebrity name to spell check")
        state = SessionState.get(flag=False)
        if (not spell_inp):
            st.write('Please enter the full name of a celebrity to get the search button')
            state.flag=False
                
        else:        
            if (st.button('Search') or state.flag ==True):
                inp = spelling_checker(spell_inp)
                celebrity_list = []
                if spell_inp == inp:
                    st.write('U have entered a proper spelling of a celebrity and we can continue with this')
                else:
                    st.write('The celebrity name close to your spelling is ' + inp + ' and we can continue with this')
                
                inp, name = process_inp(inp)
                checker = '/'+inp

                celebrity_save = pd.HDFStore('celebrity.h5')               
                try:
                    if checker in celebrity_save.keys():
                        df = celebrity_save.get(checker)
                        celebrity_save.close()
                    else:
                        dic = celebrity_func(inp, name)
                        
                        df = pd.DataFrame(dic, index=['Index'])
                    try:    
                        filepath = r".\Celebrities_Images\\" + inp +".png"
                        urlretrieve(df.loc['Index','Image_Link'], filepath)
                        image = Image.open(filepath)
                        st.image(image)
                        '''
                        Please confirm the celebrity by clicking yes or no - to get the details
                        '''
                    
                    except:
                        st.write('Image is not avaiable. please proceed with yes button to get details')
                    
                except:
                    st.write('This is not a celebrity\'s name ')
            
                state.flag = True
                cols = st.beta_columns(5)
                yes = cols[0].button('yes')
                no = cols[2].button('no')
                celebrity_save.close()
                if yes:
                    celebrity_save = pd.HDFStore('celebrity.h5')
                    celebrity_save.put(inp, df, data_columns=True)
                    celebrity_save.close()
                    found = df.index[df['Name']==name]
                    for (i, name) in df.loc[found, :].iterrows():
                        st.write(name)
                    
                if no:
                    st.write('sry!! try from beginning')
                celebrity_save.close()
                

    
    
    







