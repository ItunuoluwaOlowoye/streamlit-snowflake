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

st.set_page_config(page_title='The New Heralds Portal', page_icon=browser_tab_logo, layout='wide') # set the page layout

# for connecting to bigquery table
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])

# for connecting to google sheets
gs_credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json')

placeholder = st.empty() # create a main content placeholder
with placeholder.container(): # create a container within the placeholder
    sb_placeholder = functions.page_intro('Heralds Portal',"Please log into the Heralds Portal to input hall counts") # write the default page elements and store sidebar placeholder in a variable

if functions.authenticate_user(placeholder,sb_placeholder) and st.session_state.user.groups.filter(name__in=["Heralds"]).exists(): # after authentication and confirming that user is in heralds group
    today = date.today() # today's date
    installation = (st.session_state.user.last_name).split()[1] # store installation in a variable
    greeting,clear_cache,page_header,attendance_date,full_date,date_column,date_comment_column = functions.database_intro('Hall Counts') # default page entries
    hall_counts = functions.load_hall_counts(credentials) # load hall count data
    hall_counts = hall_counts.query(f'installation == "{installation}"') # filter to installation
    new_record, view_records = st.tabs(['Add new record', 'View previous records']) # create separate tabs for new and existing records
    with new_record: # for new records
        st.write('Verify with your check-in team if children/babies are included in the checkin database.If yes, please add that number to hall counts(adults) instead of hall counts(children).') # note this
        if attendance_date.strftime('%A') != 'Sunday': # ensure date is a sunday
            st.warning('Please select a Sunday')
        else:
            with st.form('New hall count'): # create form if date is a Sunday
                col1, col2 = st.columns(2)
                date_in = col1.date_input('Date', value=attendance_date, disabled=True) # input date
                installation_list = ['Akure','Ibadan','Ife','Ikeja','Lekki','Moro','Yaba'] # list of installations
                installation_val = col2.selectbox('Installation', installation_list, index=installation_list.index(installation),disabled=True) # input installation
                adult_count = col1.number_input('Hall count (adults)', min_value=0) # input adult hall count
                baby_count = col2.number_input('Hall count (children)', min_value=0, value=0) # input children hall count
                submitted = st.form_submit_button('Save record') # submit form
            if submitted:
                functions.save_hall_counts(credentials,gs_credentials,values=[date_in,installation_val,adult_count,baby_count]) # save data by appending to bq table
                st.experimental_rerun()
    with view_records: # show existing records
        records = hall_counts.drop(['time_filled','count_first_timers','count_not_in_db'],axis=1).sort_values('date',ascending=False).set_index('date')
        st.dataframe(records)