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

st.set_page_config(page_title='The New Service Teams Portal', page_icon=browser_tab_logo, layout='wide') # set the page layout

# for connecting to bigquery table
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])

# for connecting to google sheets
gs_credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json')

placeholder = st.empty() # create a main content placeholder
with placeholder.container(): # create a container within the placeholder
    sb_placeholder = functions.page_intro('Service Team Heads Portal',"Please log in") # write the default page elements and store sidebar placeholder in a variable

if functions.authenticate_user(placeholder,sb_placeholder) and st.session_state.user.groups.filter(name__in=["Service Team Heads"]).exists(): # after authentication and confirming that user is a service team head
    today = date.today() # today's date
    team_installation = (st.session_state.user.last_name).replace(' ','_')
    installation = team_installation.split('_')[1] # store installation in a variable
    team = team_installation.split('_')[0] # store team name in a variable
    greeting,clear_cache,page_header,attendance_date,full_date,date_column,date_comment_column = functions.database_intro(f'{team_installation} Database') # default page entries
    columns = ['full_name', date_comment_column, f'checkin_location{date_column}', 'phone_number', 'email_address', 'att_ytd', date_column, 'unique_id', 'service_team'] # columns required
    try:
        full_database = functions.load_data() # load data and store in cache
        team_database = full_database.query(f'installation == "{installation}" & service_team == "{team}"') # filter to service team data
        team_db = team_database.loc[:,columns] # select relevant columns
        unpivot_dates_df = functions.arrange_dates(team_database,columns,date_column,date_comment_column) # convert date columns to one column in olap format
    except: # when date column is not in db, throw an exception
        st.warning('Please select a Sunday')
        st.stop()
    with st.sidebar: # add a sidebar
        report_type = st.selectbox('What will you like to do?',options=['View tables','See specific attendance report','See attendance trend'])
    if report_type=='View tables': # for tables
        full_table, unaccounted_list, absent_list = st.tabs(['Full table', 'Unaccounted', 'Absentees']) # create tabs for full table, absentee and unaccounted for list
        with full_table: # for full table
            interactive_table, full_modified_df = functions.edit_table(full_database, team_db, date_column, editable_columns=[date_comment_column,'email_address','phone_number']) # create interactive table
            if full_modified_df.empty is False: # if updates are made
                save = st.button('Save updates',help='This button saves your updates and refreshes the table') # show a save button
                if save: # to save
                    functions.recalc_att_ytd(full_modified_df,today) # recalculate attendance percentage for updates
                    functions.save_data_updates(full_modified_df,credentials,date_column,group_logs=f'logs.{team_installation}') # save updates
                    functions.update_db(credentials,gs_credentials,group_logs=f'logs.{team_installation}') # update table
                    st.cache_data.clear() # clear cache
                    st.experimental_rerun() # rerun app
        with unaccounted_list:
            functions.filtered_people_list(team_db, full_date, date_column, type='unaccounted', cols=['full_name','phone_number']) # list people who have neither been marked present nor absent
        with absent_list:
            functions.filtered_people_list(team_db, full_date, date_column, type='absent', cols=['full_name','phone_number']) # list people who have been marked absent
    elif report_type=='See specific attendance report':
        st.header(f'Report: {full_date}')
        team_or_nation_numbers, total_members, last_week_full_date, todays_total_attendance, todays_present_attendance, todays_present_attendance_percent, last_week_total_attendance, last_week_present_attendance, last_week_present_attendance_percent,dataframe = functions.specific_date_summary_stats(unpivot_dates_df,attendance_date,date_column,team_or_nation=None) # calculate summary stats; dataframe only useful for checkin
        functions.specific_date_dashboard(full_date, team_or_nation_numbers, total_members, todays_total_attendance, todays_present_attendance, todays_present_attendance_percent, last_week_full_date, last_week_present_attendance) # create dashboard
    else:
        dashboard_tab,dedicated_tab,inprogress_tab,icu_tab = functions.timeseries_trends(unpivot_dates_df, columns, facet_by='full_name',tab_name='team') # create time series trends
        
