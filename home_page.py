from PIL import Image
import streamlit as st
import os
from functions import page_intro, get_img_with_href # collection of user defined functions

browser_tab_logo = Image.open('pictures/browser-tab-logo.jpg')

st.set_page_config(page_title='BuyMart Data Management', page_icon=browser_tab_logo, layout='wide') # set the page layout

page_intro('BuyMart Data Management Studio','Welcome to the data management studio. Please select your group below.')

stack1, stack2, stack3 = st.columns([1,1,1.5]) # stack of different groups

# link all pictures to url
html_dict = {}
for picture in os.listdir('pictures'):
    html_dict[picture[:-4]] = get_img_with_href('pictures/'+picture, f'https://the-new-{picture[:-4]}.streamlit.app/')

# add hyperlinked pictures to page
stack1.markdown(html_dict['checkin'], unsafe_allow_html=True)
stack1.markdown(html_dict['heralds'], unsafe_allow_html=True)
stack1.markdown(html_dict['data-team'], unsafe_allow_html=True)
stack2.markdown(html_dict['service-teams'], unsafe_allow_html=True)
stack2.markdown(html_dict['nations'], unsafe_allow_html=True)
stack2.markdown(html_dict['disciplers'], unsafe_allow_html=True)
stack3.markdown(html_dict['resident-pastors'], unsafe_allow_html=True)
stack3.markdown(html_dict['senior-pastors'], unsafe_allow_html=True)
stack3.markdown(html_dict['data-requests'],unsafe_allow_html=True)