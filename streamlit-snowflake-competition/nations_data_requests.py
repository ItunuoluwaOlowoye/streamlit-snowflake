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

st.set_page_config(page_title='The New Nations Data Requests Portal', page_icon=browser_tab_logo, layout='wide') # set the page layout

# for connecting to bigquery table
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])

# for connecting to google sheets
gs_credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json')

placeholder = st.empty() # create a main content placeholder
with placeholder.container(): # create a container within the placeholder
    sb_placeholder = functions.page_intro('Nations Data Requests Portal',"Please log in") # write the default page elements and store sidebar placeholder in a variable

# after authentication and confirming that user is a service team or nation pastor
if functions.authenticate_user(placeholder,sb_placeholder) \
    and st.session_state.user.groups.filter(name__in=["Pastor-in-charge of Nations"]).exists():
    installation = (st.session_state.user.last_name).split()[1] # store installation
    st.header('Modification Requests') # default page entries
    st.write('Please note that changes will be made within 4-5 days')
    columns = ['full_name','address','email_address','phone_number','nation','nation_head','installation'] # columns needed
    full_database = functions.load_data() # load data and store in cache
    biodata_df = full_database.loc[:,columns] # select only needed columns
    installation_biodata_df = biodata_df[biodata_df['installation']==installation] # filter to installation
    with st.sidebar:
        report_type = st.selectbox('What will you like to do?',options=['Add to nations/Modify nations', 'Remove from nations', 'Assign people to nation heads', 'Change nation head']) # select views
    if report_type=='Add to nations/Modify nations': # table view
        single_add, multiple_add = st.tabs(['Add a single nation member', 'Add multiple nation members'])
        with single_add:
            functions.modify_person_details(credentials, biodata_df, installation, df_for_modify=installation_biodata_df, modify='nation') # add member
        with multiple_add: # for multiple additions
            functions.modify_people_details(credentials, installation_biodata_df, options_df=installation_biodata_df, modify='nation')
    elif report_type=='Remove from nations': # remove workers
        single_rm, multiple_rm = st.tabs(['Remove a single nation member', 'Remove multiple nation members']) # create tabs for single or multiple additions
        with single_rm: # for single additions
            functions.modify_person_details(credentials, biodata_df, installation, df_for_modify=installation_biodata_df, modify='nation', action='deletion') # delete member
        with multiple_rm: # for multiple additions
            functions.modify_people_details(credentials, installation_biodata_df, options_df=installation_biodata_df, modify='nation', action='deletion')
    elif report_type=='Assign people to nation heads':
        nation_list = list(sorted(installation_biodata_df[installation_biodata_df['nation'].notnull()]['nation'].unique())) # select distinct available nations
        nation = st.selectbox('Select the nation', nation_list) # select the nation you want to assign tribe heads for
        nation_df = installation_biodata_df[installation_biodata_df['nation']==nation] # filter df to that nation
        single_add, multiple_add = st.tabs(['Assign a single nation member', 'Assign multiple nation members'])
        with single_add:
            functions.modify_person_details(credentials, biodata_df, installation, df_for_modify=nation_df, modify='nation_head',action='assignment') # add member
        with multiple_add: # for multiple additions
            functions.modify_people_details(credentials, nation_df, options_df=nation_df, modify='nation_head',action='assignment')
    else:
        functions.change_head(credentials, installation_biodata_df, modify='nation', head='nation_head') # change nation or team head
