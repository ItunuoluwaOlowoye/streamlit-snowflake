import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid, JsCode
import os
import base64
from django.contrib.auth import authenticate
from PIL import Image
import pandas as pd
import numpy as np
import time
from datetime import datetime,timedelta,date
import datetime as dt
import altair as alt
import pytz
import yagmail
from snowflake.connector.pandas_tools import write_pandas
from snowflake.connector import connect

utc = pytz.UTC # for time awareness

sender = 'itunu.owo@gmail.com' # mail to send emails; if this changes, don't forget to change password

snowflake_conn = connect(user='Itee', password='Itunu@snowflake23', account='qgrnfkj-mj51774', 
              database='EMPLOYEE_DATA', schema='PUBLIC', warehouse='COMPUTE_WH', role='ACCOUNTADMIN')
cursor = snowflake_conn.cursor()
    
# for bar charts
domain = ['Completed', 'incomplete', 'Unknown']
range_ = ['#8e43e7', '#6c757d', '#6c757d']

# interactive button to mark attendance
BtnCellRenderer = JsCode('''
class BtnCellRenderer {
    init(params) {
        this.params = params;
        this.eGui = document.createElement('div');
        this.eGui.innerHTML = `
         <span>
            <button id='click-button' 
                class='btn-simple' 
                style='color: ${this.params.color}; background-color: ${this.params.background_color}'>Mark</button>
         </span>
      `;

        this.eButton = this.eGui.querySelector('#click-button');

        this.btnClickedHandler = this.btnClickedHandler.bind(this);
        this.eButton.addEventListener('click', this.btnClickedHandler);

    }

    getGui() {
        return this.eGui;
    }

    refresh() {
        return true;
    }

    destroy() {
        if (this.eButton) {
            this.eGui.removeEventListener('click', this.btnClickedHandler);
        }
    }

    btnClickedHandler(event) {
        if(this.params.getValue() == 'incomplete') {
            this.refreshTable('');
            }
        else if(this.params.getValue() == 'Completed') {
            this.refreshTable('incomplete');
            }
        else {
            this.refreshTable('Completed');
            }
            console.log(this.params);
            console.log(this.params.getValue());
        }

    refreshTable(value) {
        this.params.setValue(value);
    }
};
''')

# button options for Hr
HrBtnCellRenderer = JsCode('''
class BtnCellRenderer {
    init(params) {
        this.params = params;
        this.eGui = document.createElement('div');
        this.eGui.innerHTML = `
         <span>
            <button id='click-button' 
                class='btn-simple' 
                style='color: ${this.params.color}; background-color: ${this.params.background_color}'>Mark</button>
         </span>
      `;

        this.eButton = this.eGui.querySelector('#click-button');

        this.btnClickedHandler = this.btnClickedHandler.bind(this);
        this.eButton.addEventListener('click', this.btnClickedHandler);

    }

    getGui() {
        return this.eGui;
    }

    refresh() {
        return true;
    }

    destroy() {
        if (this.eButton) {
            this.eGui.removeEventListener('click', this.btnClickedHandler);
        }
    }

    btnClickedHandler(event) {
        if(this.params.getValue() == 'Completed') {
            this.refreshTable('');
            }
        else {
            this.refreshTable('Completed');
            }
            console.log(this.params);
            console.log(this.params.getValue());
        }

    refreshTable(value) {
        this.params.setValue(value);
    }
};
''')

def resize_image(image, height):
    image_size = image.size # set the original image size to a variable
    image_width, image_height = (image_size[0], image_size[1]) # separate the width and height
    new_image_height = height # set the new image height in pixels for header/footer
    ratio = image_height/new_image_height # calculate the ratio between the original and new image height
    new_image_width = int(image_width/ratio) # calculate the new image width with the ratio
    new_image = image.resize((new_image_width,new_image_height)) # return the newly resized image
    return new_image

def get_base64_of_bin_file(bin_file): # get base64 of the pictures
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def get_img_with_href(local_img_path, target_url): # refernece local image and hyperlink to web page
    img_format = os.path.splitext(local_img_path)[-1].replace('.', '')
    bin_str = get_base64_of_bin_file(local_img_path)
    html_code = f'''
        <a href="{target_url}">
            <img src="data:image/{img_format};base64,{bin_str}" />
        </a>'''
    return html_code

def page_intro(header,body): # default page elements
    logo = Image.open('pictures/browser-tab-logo.png')
    inset_logo = resize_image(logo,30)
    logo_column, header_column = st.columns([1,25]) # create columns for logo and header; ratio needs adjustment if layout is changed to centered
    logo_column.title('')
    logo_column.image(inset_logo) # insert the body logo
    header_column.title(header) # write the header
    st.markdown(body) # write the body
    
    with st.sidebar: # add a description to the sidebar
        sb_placeholder = st.empty() # add to a container
        with sb_placeholder.container():
            st.title('BuyMart Ecommerce Store')
            st.markdown('''This is a fictitious ecommerce company that fills a weekly KPI report on Fridays.<br>
            <font style="color:#8e43e7">Report entries in this table have been randomly filled from **6th of January, 2023 to 26th of May, 2023.**</font><br>
            There is a special bonus given at the end of the year based on your weekly completion rate percentage throughout the year.<br>
            There are no breaks due to public holidays except on Christmas Day and New Year's Day''', unsafe_allow_html=True)
    return sb_placeholder # store this sidebar placeholder to a variable when calling the function

def password_entered(): # storing session usernames and passwords
    #Checks whether a password entered by the user is correct.
    user = authenticate(username=st.session_state['username'], password=st.session_state['password'])
    if user is not None: # if username is inputed
        st.session_state['password_correct'] = True # initialize storing session password
        st.session_state.user = user # add the user object to Streamlit session
    else:
        st.session_state['password_correct'] = False # don't initialize storing session password

def authenticate_user(placeholder, sb_placeholder, user_key='username', password_key='password'): # authenticate users with Django
    if 'password_correct' not in st.session_state: # first run, session password not initialized
        st.text_input('Username (this is case sensitive)', on_change=password_entered, key=user_key)
        st.text_input('Password', type='password', on_change=password_entered, key=password_key) # show inputs for username + password.
        login = st.button('Log in') # add log in button
        if login: return False # don't log in, instead save the session user credentials
        
    elif not st.session_state['password_correct']: # Password not correct, show input + error.
        st.text_input('Username (this is case sensitive)', on_change=password_entered, key=user_key)
        st.text_input('Password', type='password', on_change=password_entered, key=password_key) # show inputs for username + password.
        login = st.button('Log in') # add log in button
        if login:
            st.error('❗ User not known or password incorrect')
            return False
        
    else: # Password correct
        placeholder.empty(); sb_placeholder.empty() # clear placeholders
        return True

def database_intro(page_name:str): # default page elements after authentication
    greeting_col, cache_col = st.columns([5,1])
    greeting = greeting_col.write(f"Hello, {(st.session_state.user.first_name).title()}!") # greet the user
    clear_cache = cache_col.button('Clear cache', help='The table is stored in cache. Use this to clear cache and get current data')
    if clear_cache: st.cache_data.clear(); st.experimental_rerun()
    page_header = st.header(page_name) # write page name
    attendance_date = st.date_input('Please select the attendance date') # select attendance date
    full_date = attendance_date.strftime('%A, %d %B %Y') # full date for attendance report
    date_column = attendance_date.strftime('_%d_%b_%y').strip() # date column header
    date_comment_format = attendance_date.strftime('%d%m%Y').strip() # date format in comment columns
    date_comment_column = 'comment' + date_comment_format # date comment column
    return greeting,clear_cache,page_header,attendance_date,full_date,date_column,date_comment_column

def load_data(sort_columns=['full_name']): # load dataset and store in cache
    query = 'SELECT * from "employees"'
    cursor.execute(query)
    df = cursor.fetch_pandas_all()
    success_placeholder = st.empty() # add success message in placeholder
    success_placeholder.success('Connection to Snowflake database successful!')
    time.sleep(1)
    success_placeholder.empty()
    df = df.dropna(how='all') # drop null rows
    for column in list(df.columns): # fill null cells in columns that are not datetime or float
        if column != 'date_hired' and column != 'att_ytd':
            df[column].fillna('',inplace=True)
    df['date_hired'] = pd.to_datetime(df['date_hired'], infer_datetime_format=True) # change date column to datetime type
    df.sort_values(by=sort_columns, inplace=True) # sort by specified columns
    return df

def edit_table(full_db, dataframe, date_column, editable_columns:list): # edit interactive table
    st.markdown(f'Click on the <font style="color:#8e43e7">purple Mark button</font> in the table below to mark attendance.',unsafe_allow_html=True)
    # configure settings for the interactive table
    options_builder = GridOptionsBuilder.from_dataframe(dataframe)
    options_builder.configure_default_column(sortable=False)
    options_builder.configure_columns(editable_columns, editable=True)
    options_builder.configure_column(date_column, pinned=True, suppressSizeToFit=True, maxWidth=75)
    options_builder.configure_column('full_name', pinned=True, suppressSizeToFit=True)
    options_builder.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
    options_builder.configure_side_bar()
    grid_options = options_builder.build()
    if st.session_state.user.groups.filter(name__in=["Human Resources"]).exists(): # confirming that user is in Human Resources group
        grid_options['columnDefs'].append({"field": date_column, "header": "MarkAttendance", "pinned": True,
            "editable": False, "maxWidth":50, "cellRenderer": HrBtnCellRenderer, "cellRendererParams": {"color": "#8e43e7","background_color": "black"}
        })
    else:
        grid_options['columnDefs'].append({"field": date_column, "header": "MarkAttendance", "pinned": True,
            "editable": False, "maxWidth":50, "cellRenderer": BtnCellRenderer, "cellRendererParams": {"color": "#8e43e7","background_color": "black"}
        })
    # build interactive table
    interactive_table = AgGrid(dataframe, gridOptions=grid_options, fit_columns_on_grid_load=False, allow_unsafe_jscode=True, try_to_convert_back_to_original_types=False, enable_enterprise_modules=False)
    df = pd.DataFrame(interactive_table['data']) # convert interactive table to dataframe
    df['att_ytd'] = df['att_ytd'].astype(float)
    modified_df = df.merge(dataframe, how='left', indicator=True) # find modifications/updates
    modified_df = modified_df[modified_df['_merge'] == 'left_only'].drop('_merge',axis=1) # keep only modifications/updates
    modified_df_unique_row = modified_df['unique_id'] # select column to update full database with
    full_modified_df = full_db[full_db['unique_id'].isin(modified_df_unique_row)] # select rows for update within the full database
    full_modified_df_unique_row = full_modified_df['unique_id'] # select column to use for update in the full database
    editable_columns.append(date_column) # select columns to update
    cols_to_replace = editable_columns # select columns to update
    # update selected columns
    full_modified_df.loc[full_modified_df_unique_row.isin(modified_df_unique_row), cols_to_replace] = modified_df.loc[modified_df_unique_row.isin(full_modified_df_unique_row),cols_to_replace].values
    full_modified_df.loc[:,'date_hired'] = pd.to_datetime(full_modified_df['date_hired'], infer_datetime_format=True) # ensure date is in datetime format
    return interactive_table,full_modified_df

def recalc_att_ytd(dataframe, today): # select sundays on or before sundays
    date_list_column = [] # create list to store dates from date columns
    start_column = dataframe.columns.get_loc('_08_Jan_23') # select index of first date column
    while int(start_column) < dataframe.shape[1]: # store date columns into the list
        date_list_column.append(pd.to_datetime(dataframe.columns[start_column], format='_%d_%b_%y'))
        start_column = int(start_column) + 3
    for i in dataframe.index: # for every person in the table
        date_hired = dataframe.loc[i,'date_hired'] # select date added
        dates_available = [] # create list to store all dates in the table that are after when the user was added to the table and are on or before today
        for date in date_list_column: # for every date Completed in the original table
            if date >= date_hired and date <= pd.to_datetime(today): # check if the date is on or after the user was added and on or before today
                column_name = date.strftime('_%d_%b_%y')
                dates_available.append(column_name) # store that date into a list
        sundays_by_today = dataframe.loc[i,dates_available] # create dataframe with only those date columns
        sundays_by_today.fillna('',inplace=True)
        all_count = sundays_by_today.count() # count total days
        try:
            present_count = sundays_by_today.value_counts()['Completed'] # count days Completed
            dataframe.loc[i,'att_ytd'] = round((present_count/all_count*100),2) # recalculate att_ytd
        except: dataframe.loc[i,'att_ytd'] = 0.00
    return dataframe

def save_data_updates(dataframe,date_column,group_logs): # save the updates in a log table
    with st.spinner('Saving data...'):
        time.sleep(1.5)
        # insert log details columns
        dataframe.insert(0,'time_filled','')
        dataframe.insert(0,'user','')
        dataframe['time_filled'] = datetime.now(dt.timezone.utc)
        dataframe['user'] = st.session_state.user.username
        dataframe[f'input_location{date_column}'] = st.session_state.user.last_name
        dataframe['date_hired'] = pd.to_datetime(dataframe['date_hired'],utc=True) # ensure date added column is in the correct datatype
        success, nchunks, nrows, _ = write_pandas(conn=snowflake_conn, df=dataframe, table_name=group_logs, database='EMPLOYEE_DATA', schema='PUBLIC',auto_create_table=True)
        if st.session_state.user.groups.filter(name__in=["Human Resources"]).exists(): # confirming that user is in Human Resources group
            success_placeholder = st.empty() # add success message in placeholder
            success_placeholder.success('Data saved!')
            time.sleep(1)
            success_placeholder.empty()

def update_db(group_logs, receiver='itunu.owo@gmail.com'): # update actual data table
    with st.spinner('Refreshing table..'):
        db_query=f'SELECT * FROM "employees"'
        cursor.execute(db_query)
        df_toupdate = cursor.fetch_pandas_all()
        logs_query=f'SELECT * FROM "{group_logs}"'
        cursor.execute(logs_query)
        logs_df = cursor.fetch_pandas_all()
        logs_df = logs_df.sort_values('time_filled') # sort in ascending order by time of entry
        logs_df.drop(['user','time_filled'],axis=1,inplace=True) # drop user and time filled columns
        logs_df.drop_duplicates(['unique_id'],keep='last',inplace=True) # drop duplicate entries
        updated_df = pd.concat([df_toupdate,logs_df],axis=0,ignore_index=True) # append entries to original db
        updated_df.drop_duplicates(['unique_id'],keep='last',inplace=True) # drop duplicate entries
        try: # reconcile datetime formats
            updated_df.date_hired = pd.to_datetime(updated_df.date_hired, utc=True)
        except: # send mail to self to reconcile dates
            subject = 'date_hired field datatype mismatch'
            contents = """You are trying to save updates to the employee attendance table, however, there is
            a mismatch in the original datatype of the date_hired field and the datatype of your update. This error has been sent
            to the developer and will be fixed as soon as possible."""
            yag = yagmail.SMTP(user=sender, password='wtvkilvlkmfawnri')
            yag.send(to=receiver, subject=subject, contents=contents)
            st.warning(contents)
            time.sleep(5)
            pass
        success, nchunks, nrows, _ = write_pandas(conn=snowflake_conn, df=updated_df, table_name='employees', database='EMPLOYEE_DATA', schema='PUBLIC', auto_create_table=True, overwrite=True)
        st.success('Data updated!')

def arrange_dates(dataframe, data_columns, date_column, date_comment_column): # collate all date columns to one column for analysis purposes
    dates_list=[] # create list to store date columns
    data_columns.remove(date_column); data_columns.remove(date_comment_column) # remove date columns from data columns to keep only profile columns
    for column in dataframe.columns: # append dates to the list
        if column.startswith('_'): dates_list.append(column)
    needed_columns = data_columns+dates_list # store all columns in a variable
    unpivot_df = dataframe.loc[:,needed_columns] # select only the columns stored from the full database
    unpivot_df = pd.melt(unpivot_df, id_vars=data_columns, var_name='date', value_name='attendance') # create dataframe with dates in one column for analysis
    unpivot_df['attendance'] = unpivot_df['attendance'].replace('','Unknown')
    unpivot_df[f'input_location{date_column}'] = unpivot_df[f'input_location{date_column}'].replace('',np.nan)
    return unpivot_df

def presentcalc(dataframe): # calculate tasks Completed
    total_attendance = dataframe['attendance'].value_counts() # count total attendance
    if 'Completed' in dataframe['attendance'].unique(): # if there are tasks Completed
        present_attendance = dataframe['attendance'].value_counts()['Completed'] # count tasks Completed
        present_attendance_percent = round((dataframe['attendance'].value_counts(normalize=True)['Completed']*100),2) # calculate % of tasks Completed
    else: # tasks Completed is zero
        present_attendance, present_attendance_percent = 0, 0.0
    return total_attendance, present_attendance, present_attendance_percent

def specific_date_summary_stats(dataframe,attendance_date,dept_or_branch='dept'): # calculate summary statistics for a specific date, you can group by team or branch
    dataframe['date'] = pd.to_datetime(dataframe['date'], format='_%d_%b_%y').dt.strftime('%Y-%m-%d') # put date column in corect format
    dataframe['att_ytd'] = dataframe['att_ytd'].replace(np.nan,0) # let all attendance percent values be numeric
    selected_day_df=dataframe[dataframe['date']==str(attendance_date)] # select data from the specified date
    if dept_or_branch is None: dept_or_branch_numbers = pd.DataFrame() # empty dataframe if not grouped by team or branch
    else: dept_or_branch_numbers = selected_day_df[dept_or_branch].value_counts().to_frame() # count of team or branch
    total_members = selected_day_df['full_name'].count() # total number of tasks in selected day
    last_week=attendance_date-timedelta(days=7) # check last week
    last_week_full_date = last_week.strftime('%A, %d %B %Y').strip() # write date in full for dashboard
    last_week_df=dataframe[dataframe['date']==str(last_week)].reset_index() # select data one week from the selected day
    todays_total_attendance, todays_present_attendance, todays_present_attendance_percent = presentcalc(selected_day_df) # calculate attendance of the selected day
    last_week_total_attendance, last_week_present_attendance, last_week_present_attendance_percent = presentcalc(last_week_df) # calculate attendance of the week before selected day
    return dept_or_branch_numbers, total_members, last_week_full_date, todays_total_attendance, todays_present_attendance, todays_present_attendance_percent, last_week_total_attendance, last_week_present_attendance, last_week_present_attendance_percent

def specific_date_dashboard(full_date, dept_or_branch_numbers, total_members, todays_total_attendance, todays_present_attendance, todays_present_attendance_percent, last_week_full_date, last_week_present_attendance, head_type='total'): # create a dashboard of the summary statistics
    delta = int(todays_present_attendance-last_week_present_attendance) # calculate difference between specified date and week before attendance
    abs_delta = abs(delta) # store absolute value of difference
    relativity = '' # initialize a variable to store comparisons
    if todays_present_attendance_percent >= 70: st.balloons(); message = 'Congratulations!' # add congratulatory message if attendance is more than 70 percent
    else: message=''
    if dept_or_branch_numbers.empty: pass
    else: 
        numbers_expander=st.expander(f'Are the {head_type}s under/over staffed or optimal?') # check numbers per group
        numbers_expander.dataframe(dept_or_branch_numbers)   
    scorecard_column, tablechart_column, percent_columns = st.columns([1,1.25,1]) # create three different columns for dashboard
    # create scorecard chart
    scorecard_column.metric(label=f'Your {head_type} in Weekly Report today', value=todays_present_attendance,
    delta=delta, help='Compare attendance with last week. The smaller-sized number below shows by how much attendance increased (green) or decreased (red) compared to last week.')
    # create expander for bar chart
    chart_expander=tablechart_column.expander("See attendance chart:")
    with chart_expander:
        st.markdown(f'Attendance summary for {full_date}')
        # show bar chart for attendance
        chart = (alt.Chart(todays_total_attendance.reset_index())
        .mark_bar()
        .encode(x=alt.X('attendance', axis=alt.Axis(labels=False)), y=alt.Y('index', axis=alt.Axis(title=None), sort=domain),
        color=alt.Color('index', scale=alt.Scale(domain=domain, range=range_), legend=None)))
        text = chart.mark_text(align='left', baseline='middle', dx=3).encode(text='attendance')
        st.altair_chart(chart+text,use_container_width=True)
    # create expander for table
    table_expander = tablechart_column.expander("See summary table:")
    with table_expander:
        st.markdown(f"Summary table for {full_date}")
        st.dataframe(todays_total_attendance) # show table
    # write percentage attendance
    percent_columns.markdown(f'''{message} <font style="color:#8e43e7;font-size:20px;"><strong>{todays_present_attendance_percent}%</strong></font>   of your {head_type} members were in 
    Weekly Report today.''', unsafe_allow_html=True)
    # create summary paragraph
    st.markdown(f'''###### Summary Paragraph:''')
    if delta>0: # specified date attendance more than last week attendance
        relativity = 'more than'; color=':green'
    elif delta<0: # specified date attendance less than last week attendance
        relativity = 'less than'; color=':red'
    else: # specified date attendance and previous week attendance are the same
        abs_delta=''; relativity = 'the same as'; color=':white'
    st.markdown(f'''In summary, you have **{total_members}** {head_type} members. 
    <font style="color:#8e43e7">{todays_present_attendance}</font> of them completed their tasks in Weekly Report today and this is {abs_delta} {color}[{relativity} last week] {last_week_full_date}.
    ''', unsafe_allow_html=True)

def bar_facets(dataframe,attendance_date,full_date,facet_by,number_of_facets): # create bar chart groups/facets
    title = str(facet_by).replace('_', ' ').title() # change facet name to proper case
    facet_data=dataframe[dataframe['date']==str(attendance_date)] # select specified date from data table
    facet_data=pd.DataFrame(facet_data.groupby(facet_by)['attendance'].value_counts()) # group by column selected to facet by
    facet_data=facet_data.rename(columns={'attendance':'count'}).reset_index() # rename attendance column to count and reset index
    # build chart with altair library
    chart = (alt.Chart(facet_data, title=f'Attendance summary for {full_date}')
             .mark_bar()
             .encode(x=alt.X('count', axis=alt.Axis(labels=True, title=None)), 
                     y=alt.Y('attendance', axis=alt.Axis(title=None), sort=domain),
                     color=alt.Color('attendance', scale=alt.Scale(domain=domain, range=range_), legend=None),
                     facet=alt.Facet(facet_by, columns=number_of_facets, title=title))
             .properties(width=180, height=90)).configure_header(titleColor='#6c757d',titleFontSize=14,labelColor='#8e43e7', labelFontSize=14)
    # create expanders for table and bar chart in separate columns
    facets_table = st.expander(f'View attendance table by: {title}')
    facets_table.write(facet_data)
    try:
        facets_chart = st.expander(f'View attendance charts by: {title}')
        facets_chart.altair_chart(chart)
    except: pass

def filtered_people_list(dataframe, full_date, date_column, type:str, cols:list): # filter dataframe for incomplete and unaccounted for tasks
    cols.append(date_column)
    df_subset = dataframe.loc[:,cols]  # select revelant columns
    if type.title()=='Unaccounted': # for unaccounted tasks
        st.write(f'tasks unaccounted for in Weekly Report on {full_date}')
        df = df_subset[(df_subset[date_column] != 'incomplete') & (df_subset[date_column] != 'Completed')].reset_index(drop=True) # filter to tasks who have neither been recorded as Completed or incomplete
    elif type.title()=='incomplete': # for incomplete tasks
        st.write(f'tasks {type.lower()} in Weekly Report on {full_date}')
        df = df_subset[df_subset[date_column] == type.title()].reset_index(drop=True) # filter to tasks who have been marked incomplete
    st.dataframe(df) # show dataframe

def attendance_metric(dataframe,columns,att_percent_query): # select tasks with attendance of a certain percentage
    att = dataframe.query(att_percent_query) 
    att = att.loc[:,columns] # return specified columns
    return att

def timeseries_trends(dataframe, columns, facet_by='region',tab_name='team'): # create a time series trends section
    # convert date column to datetime format
    try: dataframe['date'] = pd.to_datetime(dataframe['date'])
    except: dataframe['date'] = pd.to_datetime(dataframe['date'], format='_%d_%b_%y')
    individual_att_ytd = dataframe.drop(['date','attendance'], axis=1).drop_duplicates() # drop the date and attendance columns and select unique records
    poor_attendance = attendance_metric(individual_att_ytd, columns, att_percent_query='att_ytd < 50.00') # identify tasks with poor attendance
    good_attendance = attendance_metric(individual_att_ytd, columns, att_percent_query='att_ytd >= 70.00') # identify tasks with good attendance
    average_attendance = attendance_metric(individual_att_ytd, columns, att_percent_query='att_ytd >=50.00 & att_ytd<70.00') # identify tasks with average attendance
    dashboard_tab, dedicated_tab, inprogress_tab, icu_tab = st.tabs(['Attendance trends', f'Dedicated {tab_name}', f'{tab_name.title()}-in-progress', f'ICU {tab_name}']) # create seperate tabs for the different stats
    with dashboard_tab: # for time series dashboard
        intro_column, start_column, and_column, end_column = st.columns(4) # create columns for filtering date inputs
        intro_column.header(''); intro_column.markdown(f'Pick a day between') # write
        start_date = start_column.date_input('start date', value=date(2023,1,1)) # create date input for start date, with default as 1st of January
        start_datetime = pd.to_datetime(start_date) # convert start date to datetime format
        and_column.header(''); and_column.markdown(f' and ') # write
        end_date=end_column.date_input('end date', key='end', value=date.today()) # create date input for end date, default as today's date
        end_datetime = pd.to_datetime(end_date) # convert end date to datetime format
        filtered_dates = dataframe.loc[(dataframe['date']>=start_datetime) & (dataframe['date']<=end_datetime)] # filter data to entries between start and end dates, both inclusive
        filtered_linechart_data = filtered_dates.groupby(['date','attendance'])['full_name'].count().reset_index().query('attendance == "Completed"') # group by date and attendance and select Completed attendance
        mean_att = round(filtered_linechart_data['full_name'].mean()) # calculate mean
        st.header(''); mean_column, trend_column = st.columns([1.5,4]) # create columns for mean and line chart
        mean_column.write(f'You have {len(individual_att_ytd)} tasks to account for.') # write how many tasks to account for
        mean_column.metric('Average attendance', value=mean_att, help='Average attendance over the selected timeframe') # write mean metric
        with trend_column: # create line chart
            chart = alt.Chart(filtered_linechart_data).mark_line(color='#8e43e7')\
            .encode(x=alt.X('date:T', axis=alt.Axis(title=None)),
                    y=alt.Y('full_name', axis=alt.Axis(title='Attendees')),
                    tooltip=['date:T', 'full_name'])
            st.altair_chart(chart, use_container_width=True)
        if facet_by == 'full_name': faceted_linechart_data = filtered_dates.groupby(['date',facet_by,'attendance']).count().reset_index().query('attendance == "Completed"') # aggregating by names
        else: # otherwise; also create faceted chart in an expander
            faceted_linechart_data = filtered_dates.groupby(['date',facet_by,'attendance'])['full_name'].count().reset_index().query('attendance == "Completed"')
            faceted_linechart_data = faceted_linechart_data.pivot(index=facet_by,columns='date', values='full_name')
            faceted_linechart_data = faceted_linechart_data.replace(np.nan,0).reset_index()
            faceted_linechart_data = pd.melt(faceted_linechart_data, id_vars=[facet_by], var_name='date', value_name='full_name')
            title = str(facet_by).replace('_',' ').title()
            chart = (alt.Chart(faceted_linechart_data).mark_line(color='#8e43e7')
                     .encode(x=alt.X('date:T', axis=alt.Axis(title=None)), 
                             y=alt.Y('full_name', axis=alt.Axis(title='Attendees')), 
                             tooltip=['date:T', 'full_name'], facet=alt.Facet(facet_by, columns=3, title=title))
                    .properties(width=180, height=90)).configure_header(titleColor='#6c757d',
                                                                        titleFontSize=14, 
                                                                        labelColor='#8e43e7',
                                                                        labelFontSize=14)
            chart_expander = st.expander(f'View trends by: {title}')
            chart=chart_expander.altair_chart(chart)
    with dedicated_tab: # for dedicated attendees
        st.success((f'You have {good_attendance.shape[0]} dedicated people'))
        # create table of count per group
        attendance_count = good_attendance[facet_by].value_counts().to_frame().reset_index().rename(columns={'index':f'{facet_by}', f'{facet_by}':'count'})
        st.dataframe(attendance_count)
    with inprogress_tab: # for average attendees
        st.warning(f'You have {average_attendance.shape[0]} people on the fence')
        # create table of count per group
        attendance_count = average_attendance[facet_by].value_counts().to_frame().reset_index().rename(columns={'index':f'{facet_by}', f'{facet_by}':'count'})
        st.dataframe(attendance_count)
    with icu_tab: # for poor attendees
        st.error(f'You have {poor_attendance.shape[0]} ICU patients')
        # create table of count per group
        attendance_count = poor_attendance[facet_by].value_counts().to_frame().reset_index().rename(columns={'index':f'{facet_by}', f'{facet_by}':'count'})
        st.dataframe(attendance_count)
    return dashboard_tab,dedicated_tab,inprogress_tab,icu_tab

def wrong_portal():
    st.info('''You have access to the BuyMart database, however, you seem to have accessed a portal that you do not have access to. Please redirect to the correct portal for your level/role. Thank you.
    The page url is written in the format, **https://buy-mart-<portal-name>-streamlit.app**.
    Are you on the right portal?''')

