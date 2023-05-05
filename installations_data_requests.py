import streamlit as st
import streamlit as st
from django.core.wsgi import get_wsgi_application
import os
from datetime import date
from google.oauth2 import service_account
from PIL import Image
from oauth2client.service_account import ServiceAccountCredentials
import functions # a collection of user defined functions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings') # set up Django environment and application
application = get_wsgi_application()

browser_tab_logo = Image.open('pictures/browser-tab-logo.jpg') # store tab logo in a variable

st.set_page_config(page_title='The New Data Requests Portal', page_icon=browser_tab_logo, layout='wide') # set the page layout

# for connecting to bigquery table
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])

# for connecting to google sheets
gs_credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json')

placeholder = st.empty() # create a main content placeholder
with placeholder.container(): # create a container within the placeholder
    sb_placeholder = functions.page_intro('Installations Data Requests Portal',"Please log in") # write the default page elements and store sidebar placeholder in a variable

# after authentication and confirming that user is a resident pastor
if functions.authenticate_user(placeholder,sb_placeholder) \
    and st.session_state.user.groups.filter(name__in=["Resident Pastors"]).exists():
    installation = (st.session_state.user.last_name).split()[1] # store installation
    st.header('Modification Requests') # default page entries
    st.write('Please note that changes will be made within 4-5 days')
    columns = ['full_name','installation','email_address','phone_number','service_team','nation','unique_id'] # columns needed
    full_database = functions.load_data() # load data and store in cache
    biodata_df = full_database.loc[:,columns] # select only needed columns
    installation_biodata_df = biodata_df[biodata_df['installation']==installation] # filter to installation
    other_installation_biodata_df = biodata_df[biodata_df['installation']!=installation] # filter to other installation
    with st.sidebar:
        report_type = st.selectbox('What will you like to do?',options=['Transfer to other installation', 'Add from another installation']) # select views
    if report_type=='Transfer to other installation': # transfer
        st.write('Please liaise with the former installation to ensure that a corresponding addition request is made')
        single_add, multiple_add = st.tabs(['Transfer a single person', 'Transfer multiple people'])
        with single_add:
            functions.modify_person_details(credentials, biodata_df, installation, df_for_modify=biodata_df, modify='installation', action='transfer') # add member
        with multiple_add: # for multiple additions
            functions.modify_people_details(credentials, installation_biodata_df, options_df=other_installation_biodata_df, modify='installation', action='transfer')
    elif report_type=='Add from another installation': # add
            st.write('Please liaise with the former installation to ensure that a corresponding transfer request is made')
            single_add, multiple_add = st.tabs(['Add a single person', 'Add multiple people'])
            with single_add:
                functions.modify_single_installation_details(credentials, biodata_df, installation, df_for_modify=installation_biodata_df, modify='installation', action='addition') # modify single person's installation
            with multiple_add: # for multiple additions
                functions.modify_people_details(credentials, other_installation_biodata_df, options_df=installation_biodata_df, modify='installation', action='addition')
