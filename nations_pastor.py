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

st.set_page_config(page_title='The New Nations Pastor Portal', page_icon=browser_tab_logo, layout='wide') # set the page layout

# for connecting to bigquery table
credentials = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])

# for connecting to google sheets
gs_credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json')

placeholder = st.empty() # create a main content placeholder
with placeholder.container(): # create a container within the placeholder
    sb_placeholder = functions.page_intro('Nations Pastor Portal',"Please log in as Pastor in charge of Nations") # write the default page elements and store sidebar placeholder in a variable

if functions.authenticate_user(placeholder,sb_placeholder) and st.session_state.user.groups.filter(name__in=["Pastor-in-charge of Nations"]).exists(): # after authentication and confirming that user is a service team pastor
    today = date.today() # today's date
    church_nation = (st.session_state.user.last_name).replace(' ','_')
    installation = church_nation.split('_')[1] # store installation in a variable
    greeting,clear_cache,page_header,attendance_date,full_date,date_column,date_comment_column = functions.database_intro(f'{church_nation} Database') # default page entries
    columns = ['full_name', 'nation', f'checkin_location{date_column}', date_comment_column, 'phone_number', 'email_address', 'att_ytd', date_column, 'unique_id', 'nation_head'] # columns required
    try:
        full_database = functions.load_data() # load full data and store in cache
        nations_database = full_database.query(f'installation == "{installation}" & nation != ""') # select service teams within installation
        nations_db = nations_database.loc[:,columns].sort_values(['nation','full_name']) # filter to relevant columns
        unpivot_dates_df = functions.arrange_dates(nations_database,columns,date_column,date_comment_column) # convert date columns to one column in olap format
    except:
        st.warning('Please select a Sunday') # if date selected is not in the columns, throw an error
        st.stop()
    with st.sidebar:
        report_type = st.selectbox('What will you like to do?',options=['View tables','See specific attendance report','See attendance trend']) # sidebar options
    if report_type=='View tables': # to view tables
        full_table, unaccounted_list, absent_list = st.tabs(['Full table', 'Unaccounted', 'Absentees']) # create tabs for table, absentee list, and unaccounted list
        with full_table: # for full table
            interactive_table, full_modified_df = functions.edit_table(full_database, nations_db, date_column, editable_columns=[date_comment_column,'phone_number','email_address']) # create interactive table
            if full_modified_df.empty is False: # if updates are made
                save = st.button('Save updates',help='This button saves your updates and refreshes the table') # show a save button
                if save: # save button
                    functions.recalc_att_ytd(full_modified_df,today) # recalculate attendance percentage
                    functions.save_data_updates(full_modified_df,credentials,date_column,group_logs=f'logs.{church_nation}') # save to bqtable
                    functions.update_db(credentials,gs_credentials,group_logs=f'logs.{church_nation}') # update original db
                    st.cache_data.clear() # clear cache
                    st.experimental_rerun() # rerun app
        with unaccounted_list: # for unaccounted people
            functions.filtered_people_list(nations_db, full_date, date_column, type='unaccounted', cols=['full_name','nation','phone_number']) # select unaccounted members from table
        with absent_list: # for absent people
            functions.filtered_people_list(nations_db, full_date, date_column, type='absent', cols=['full_name','nation','phone_number',date_comment_column]) # select absent people from list
    elif report_type=='See specific attendance report': # for attendance report
        st.header(f'Report: {full_date}') # header
        team_or_nation_numbers, total_members, last_week_full_date, todays_total_attendance, todays_present_attendance, todays_present_attendance_percent, last_week_total_attendance, last_week_present_attendance, last_week_present_attendance_percent,dataframe = functions.specific_date_summary_stats(unpivot_dates_df,attendance_date,date_column,team_or_nation='nation') # calculate summary stats; dataframe only useful for checkin
        functions.specific_date_dashboard(full_date, team_or_nation_numbers, total_members, todays_total_attendance, todays_present_attendance, todays_present_attendance_percent, last_week_full_date, last_week_present_attendance, head_type='nation') # create dashboard
        functions.bar_facets(unpivot_dates_df,attendance_date,full_date,facet_by='nation',number_of_facets=3) # show stats grouped by service team
    else: # for trends
        dashboard_tab,dedicated_tab,inprogress_tab,icu_tab = functions.timeseries_trends(unpivot_dates_df, columns, facet_by='nation',tab_name='nation') # show timeseries trends
        
