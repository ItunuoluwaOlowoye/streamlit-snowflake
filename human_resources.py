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

browser_tab_logo = Image.open('pictures/browser-tab-logo.png') # store tab logo in a variable

st.set_page_config(page_title='The New Checkin Portal', page_icon=browser_tab_logo, layout='wide') # set the page layout

placeholder = st.empty() # create a main content placeholder
with placeholder.container(): # create a container within the placeholder
    sb_placeholder = functions.page_intro('Human Resources Portal',"This portal is only accessible to HR (human resources) staff. This is where attendance for Sunday operations is logged by HR.") # write the default page elements and store sidebar placeholder in a variable

if functions.authenticate_user(placeholder,sb_placeholder) and st.session_state.user.groups.filter(name__in=["Check-in Team"]).exists(): # after authentication and confirming that user is in checkin group
    today = date.today() # today's date
    checkin_location = (st.session_state.user.last_name).split()[1] # store checkin location in a variable
    greeting,clear_cache,page_header,attendance_date,full_date,date_column,date_comment_column = functions.database_intro('Checkin Database') # default page entries
    columns = ['full_name','installation','email_address','phone_number','att_ytd',date_column,date_comment_column,'unique_id'] # columns needed
    try:
        full_database = functions.load_data() # load data and store in cache
        checkin_df = full_database.loc[:,columns] # select only needed columns
        columns.append(f'checkin_location{date_column}') # include checkin location column
        unpivot_dates_df = functions.arrange_dates(full_database,columns,date_column,date_comment_column) # convert date columns to one column in olap format
        team_or_nation_numbers, total_members, last_week_full_date, todays_total_attendance, todays_present_attendance, todays_present_attendance_percent, last_week_total_attendance, last_week_present_attendance, last_week_present_attendance_percent, checkin_olap_df = functions.specific_date_summary_stats(unpivot_dates_df,attendance_date,date_column,team_or_nation=None) # calculate summary stats
    except:
        st.warning('Please select a Sunday') # if date selected is not in the columns, throw an error
        st.stop() # stop execution until error is fixed
    with st.sidebar:
        report_type = st.selectbox('What will you like to do?',options=['View tables','Checkin vs. Hall Count Variance','See specific attendance report','See attendance trend']) # select views
    if report_type=='View tables': # table view
        name_search = st.text_input('What name are you searching for?').lower() # input to search for names
        filtered_checkin_df = checkin_df[checkin_df['full_name'].str.lower().str.contains(name_search)] # filter table to name search
        interactive_table, full_modified_df = functions.edit_table(full_database, filtered_checkin_df, date_column, editable_columns=[date_comment_column]) # create interactive table
        functions.recalc_att_ytd(full_modified_df,today) # recalculate att for updates
        if full_modified_df.empty is False: # if updates exist
            functions.save_data_updates(full_modified_df,credentials,date_column,group_logs=f'logs.Checkin_{checkin_location}') # append to bigquery
        st.write('Please refresh the table at the end of your session to view updates')
        refresh = st.button('Refresh table') # include button to refresh original db
        if refresh:
            functions.update_db(credentials,gs_credentials,group_logs=f'logs.Checkin_{checkin_location}') # refresh original db with updates and also connected Google Sheet
            st.cache_data.clear() # clear cache
            st.experimental_rerun() # rerun app to get latest updates
    elif report_type=='Checkin vs. Hall Count Variance': # for variance between checkin and hall count
        hall_counts = functions.load_hall_counts(credentials) # load hall count data
        todays_hall_count = hall_counts[hall_counts['date']==attendance_date] # select hall count data for selected date
        fill_data_expander = st.expander("Fill first timer and not in database numbers if you haven't already done so") # create expander for first timers and not in database numbers
        with fill_data_expander: # input and save first timers and not in db numbers
            ft_col, nidb_col = st.columns(2) # create two columns
            first_timers = ft_col.number_input('How many first timers did you have today?',min_value=0, value=0) # save first timer number in a variable
            not_in_db = nidb_col.number_input('How many people were not in db?', min_value=0, value=0) # save not in db number in a variable
            save = st.button('Save')
            if save: # save data, throw warning if error
                try: functions.save_checkin_firsttimers_notindb(todays_hall_count,checkin_location,first_timers,not_in_db,credentials)
                except: st.warning('Hall count data is invalid for your installation. Please check with your Heralds team')
        try: # calculate variance; throw warning if error
            functions.hall_count_variance(unpivot_dates_df,attendance_date,credentials,group_by_column=f'checkin_location{date_column}')
            st.warning('Have you filled and saved your first timer numbers and not in db yet? Please do.')
        except: st.warning('No checkin data for this date available yet')
    elif report_type=='See specific attendance report': # for attendance report
        st.header(f'Report: {full_date}')
        functions.specific_date_dashboard(full_date, team_or_nation_numbers, total_members, todays_total_attendance, todays_present_attendance, todays_present_attendance_percent, last_week_full_date, last_week_present_attendance) # create dashboard
        functions.bar_facets(checkin_olap_df,attendance_date,full_date,facet_by=f'checkin_location{date_column}',number_of_facets=3) # show stats grouped by checkin location
        functions.bar_facets(checkin_olap_df,attendance_date,full_date,facet_by=[f'checkin_location{date_column}','installation'],number_of_facets=3) # show stats grouped by checkin location and installation
        functions.bar_facets(checkin_olap_df,attendance_date,full_date,facet_by='installation',number_of_facets=3) # show stats grouped by installation
    else: # create time series trends
        dashboard_tab,dedicated_tab,inprogress_tab,icu_tab = functions.timeseries_trends(checkin_olap_df, columns, facet_by='installation',tab_name='attendees')