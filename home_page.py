# import relevant packages
import streamlit as st
import os
from PIL import Image
import base64
# import user-defined functions script
import functions

# open an image and save it as a variable
logo = Image.open('pictures/browser-tab-logo.png')
# set the app page's title, icon, and layout
st.set_page_config(page_title='BuyMart Data Management', 
										page_icon= logo, 
										layout='wide')

# set up default elements
functions.page_intro(image=logo, header='BuyMart Data Management Studio',
					body='Welcome to the data management studio. Please select your group below.')

# create three columns with the first and third slightly larger than the middle
stack1, stack2, stack3 = st.columns([1.2,1,1.2])

# create a dictionary to store hyperlinks
html_dict = {}

# for each picture in the pictures directory, create the hyperlink
for picture in os.listdir('pictures'):
	picture_name = picture[:-4] # remove the .png/.jpg from the picture name
	html_dict[picture_name] = functions.hyperlink_html('pictures/'+picture, f'https://buy-mart-{picture_name}.streamlit.app/')

# add hyperlinked pictures to page
stack1.markdown(html_dict['human-resources'], unsafe_allow_html=True)
stack2.markdown(html_dict['branches'], unsafe_allow_html=True)
stack3.markdown(html_dict['departments'], unsafe_allow_html=True)