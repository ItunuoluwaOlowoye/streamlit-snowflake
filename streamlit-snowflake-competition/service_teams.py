import streamlit as st
from django.core.wsgi import get_wsgi_application
import os
from datetime import date
from google.oauth2 import service_account
from PIL import Image
from oauth2client.service_account import ServiceAccountCredentials
from functions import page_intro, get_img_with_href # collection of user defined functions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings') # set up Django environment and application
application = get_wsgi_application()

browser_tab_logo = Image.open('pictures/browser-tab-logo.jpg') # store tab logo in a variable

st.set_page_config(page_title='The New Service Teams Portal', page_icon=browser_tab_logo, layout='wide') # set the page layout

page_intro('The New Service Teams','Welcome to Service Teams. Please select your group below.')

stack1, stack2, stack3 = st.columns([1,1,1.5]) # stack of different groups

# link all pictures to url
html_dict = {}
for picture in os.listdir('pictures'):
    html_dict[picture[:-4]] = get_img_with_href('pictures/'+picture, f'https://the-new-{picture[:-4]}.streamlit.app/')

# add hyperlinked pictures to page
stack1.markdown(html_dict['service-team-heads'], unsafe_allow_html=True)
stack2.markdown(html_dict['service-teams-pastor'], unsafe_allow_html=True)