from PIL import Image
import streamlit as st
import os
from functions import page_intro, get_img_with_href # collection of user defined functions

logo = Image.open('pictures/browser-tab-logo.png')

st.set_page_config(page_title='BuyMart Data Management', page_icon=logo, layout='wide') # set the page layout

page_intro(logo, 'BuyMart Data Management Studio','Welcome to the data management studio. Please select your group below.')

stack1, stack2, stack3 = st.columns([1.2,1,1.2]) # stack of different groups

# link all pictures to url
html_dict = {}
for picture in os.listdir('pictures'):
    html_dict[picture[:-4]] = get_img_with_href('pictures/'+picture, f'https://buy-mart-{picture[:-4]}.streamlit.app/')

# add hyperlinked pictures to page
stack1.markdown(html_dict['human-resources'], unsafe_allow_html=True)
stack2.markdown(html_dict['branches'], unsafe_allow_html=True)
stack3.markdown(html_dict['departments'], unsafe_allow_html=True)
