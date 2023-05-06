import streamlit as st
from django.core.wsgi import get_wsgi_application
import os
from datetime import date
from PIL import Image
import functions # a collection of user defined functions

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings') # set up Django environment and application
application = get_wsgi_application()

browser_tab_logo = Image.open('pictures/browser-tab-logo.png') # store tab logo in a variable

st.set_page_config(page_title='BuyMart Human Resources Portal', page_icon=browser_tab_logo, layout='wide') # set the page layout

placeholder = st.empty() # create a main content placeholder
with placeholder.container(): # create a container within the placeholder
    sb_placeholder = functions.page_intro('Human Resources Portal',f"This portal is only accessible to HR (human resources) staff. This is where attendance for Sunday operations is logged by HR. You can find the list of usernames and passwords [here]()") # write the default page elements and store sidebar placeholder in a variable
    
if functions.authenticate_user(placeholder,sb_placeholder):
    if st.session_state.user.groups.filter(name__in=["Human Resources"]).exists(): # after authentication and confirming that user is in hr group
        today = date.today() # today's date
        checkin_location = (st.session_state.user.last_name).split()[1] # store hr location in a variable
        greeting,clear_cache,page_header,attendance_date,full_date,date_column,date_comment_column = functions.database_intro('HR Database') # default page entries
        columns = ['full_name','region','email_address','phone_number','att_ytd',date_column,date_comment_column,'unique_id'] # columns needed
        try:
            full_database = functions.load_data() # load data and store in cache
            checkin_df = full_database.loc[:,columns] # select only needed columns
            columns.append(f'checkin_location{date_column}') # include hr location column
            unpivot_dates_df = functions.arrange_dates(full_database,columns,date_column,date_comment_column) # convert date columns to one column in olap format
            team_or_nation_numbers, total_members, last_week_full_date, todays_total_attendance, todays_present_attendance, todays_present_attendance_percent, last_week_total_attendance, last_week_present_attendance, last_week_present_attendance_percent = functions.specific_date_summary_stats(unpivot_dates_df,attendance_date,team_or_nation=None) # calculate summary stats
        except:
            st.warning('Please select a Sunday') # if date selected is not in the columns, throw an error
            st.stop() # stop execution until error is fixed
        with st.sidebar:
            report_type = st.selectbox('What will you like to do?',options=['View tables','See specific attendance report','See attendance trend']) # select views
        if report_type=='View tables': # table view
            name_search = st.text_input('What name are you searching for?').lower() # input to search for names
            filtered_checkin_df = checkin_df[checkin_df['full_name'].str.lower().str.contains(name_search)] # filter table to name search
            interactive_table, full_modified_df = functions.edit_table(full_database, filtered_checkin_df, date_column, editable_columns=[date_comment_column]) # create interactive table
            functions.recalc_att_ytd(full_modified_df,today) # recalculate att for updates
            if full_modified_df.empty is False: # if updates exist
                functions.save_data_updates(full_modified_df,date_column,group_logs=f'HR_{checkin_location}') # append to snowflake db
            st.write('Please refresh the table at the end of your session to view updates')
            refresh = st.button('Refresh table') # include button to refresh original db
            if refresh:
                functions.update_db(group_logs=f'HR_{checkin_location}') # refresh original db with updates and also connected Google Sheet
                st.cache_data.clear() # clear cache
                st.experimental_rerun() # rerun app to get latest updates
        elif report_type=='See specific attendance report': # for attendance report
            st.header(f'Report: {full_date}')
            functions.specific_date_dashboard(full_date, team_or_nation_numbers, total_members, todays_total_attendance, todays_present_attendance, todays_present_attendance_percent, last_week_full_date, last_week_present_attendance) # create dashboard
            functions.bar_facets(unpivot_dates_df,attendance_date,full_date,facet_by=f'checkin_location{date_column}',number_of_facets=3) # show stats grouped by hr location
            functions.bar_facets(unpivot_dates_df,attendance_date,full_date,facet_by='region',number_of_facets=3) # show stats grouped by region
        else: # create time series trends
            dashboard_tab,dedicated_tab,inprogress_tab,icu_tab = functions.timeseries_trends(unpivot_dates_df, columns, facet_by='region',tab_name='attendees')
        st.stop()
    else:
        st.warning('You have access to the BuyMart database, however, you seem to have accessed a portal that you do not have access to. Please redirect to the correct portal for your level/role. Thank you')