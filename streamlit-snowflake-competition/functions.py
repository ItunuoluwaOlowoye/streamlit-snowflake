import streamlit as st
from st_aggrid import GridOptionsBuilder, AgGrid, JsCode
import os
import base64
from django.contrib.auth import authenticate
from PIL import Image
import pandas as pd
import pandas_gbq
import numpy as np
import time
from datetime import datetime,timedelta,date
import altair as alt
import gspread as gs
import pytz
import yagmail
from io import BytesIO

utc = pytz.UTC # for time awareness

sender = 'itunu.owo@gmail.com' # mail to send emails; if this changes, don't forget to change password

# for bar charts
domain = ['Present', 'Absent', 'Unknown']
range_ = ['#FFC533', 'grey', 'grey']

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
        if(this.params.getValue() == 'Absent') {
            this.refreshTable('');
            }
        else if(this.params.getValue() == 'Present') {
            this.refreshTable('Absent');
            }
        else {
            this.refreshTable('Present');
            }
            console.log(this.params);
            console.log(this.params.getValue());
        }

    refreshTable(value) {
        this.params.setValue(value);
    }
};
''')

# button options for checkin
CheckinBtnCellRenderer = JsCode('''
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
        if(this.params.getValue() == 'Present') {
            this.refreshTable('');
            }
        else {
            this.refreshTable('Present');
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
    logo = Image.open('pictures/the-new-logo.png')
    inset_logo = resize_image(logo,30)
    logo_column, header_column = st.columns([1,25]) # create columns for logo and header; ratio needs adjustment if layout is changed to centered
    logo_column.title('')
    logo_column.image(inset_logo) # insert the body logo
    header_column.title(header) # write the header
    st.write(body) # write the body
    
    with st.sidebar: # add the creed to the sidebar
        sb_placeholder = st.empty() # add to a container
        with sb_placeholder.container():
            st.title('The Creed')
            st.markdown('''I am The New<br>I have no taste for mere religion without change<br>
            I live a purpose-driven, result-oriented life based on principles in God's Word<br>I'm a man of the Word, yielded to the Spirit, and committed to God's purpose for my life<br>
            I take my place in God's army and in His agenda for the Earth and my generation<br>I bring great joy to my city<br>
            As sure as God helps me,<br>I will not give up,<br>I will not cave in,<br>
            I will not quit,<br>I will not fear,<br>I will not fail,<br>I will not die,<br>
            Until my job is done and victory is won.<br>I am the New and I love this church!''', unsafe_allow_html=True)
    return sb_placeholder # store this sidebar placeholder to a variable when calling the function

def password_entered(): # storing session usernames and passwords
    #Checks whether a password entered by the user is correct.
    user = authenticate(username=st.session_state['username'], password=st.session_state['password'])
    if user is not None: # if username is inputed
        st.session_state['password_correct'] = True # initialize storing session password
        st.session_state.user = user # add the user object to Streamlit session
    else:
        st.session_state['password_correct'] = False # don't initialize storing session password

def authenticate_user(placeholder, sb_placeholder): # authenticate users with Django
    if 'password_correct' not in st.session_state: # first run, session password not initialized
        st.text_input('Username (this is case sensitive)', on_change=password_entered, key='username')
        st.text_input('Password', type='password', on_change=password_entered, key='password') # show inputs for username + password.
        login = st.button('Log in') # add log in button
        if login: return False # don't log in, instead save the session user credentials
        
    elif not st.session_state['password_correct']: # Password not correct, show input + error.
        st.text_input('Username (this is case sensitive)', on_change=password_entered, key='username')
        st.text_input('Password', type='password', on_change=password_entered, key='password') # show inputs for username + password.
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

@st.cache_data(ttl=3*60*60) # cache for three hours
def load_data(file_path='gs://the_new_global_db/the_new_global.csv',sort_columns=['full_name']): # load dataset and store in cache
    df = pd.read_csv(file_path, storage_options={'token':'credentials.json'}) # read data from GCP bucket
    df = df.dropna(how='all') # drop null rows
    for column in list(df.columns): # fill null cells in columns that are not datetime or float
        if column != 'date_added' and column != 'att_ytd':
            df[column].fillna('',inplace=True)
    df['date_added'] = pd.to_datetime(df['date_added'], infer_datetime_format=True) # change date column to datetime type
    df['phone_number'] = df['phone_number'] # change phone number to string
    df.sort_values(by=sort_columns, inplace=True) # sort by specified columns
    return df

def edit_table(full_db, dataframe, date_column, editable_columns:list): # edit interactive table
    # configure settings for the interactive table
    options_builder = GridOptionsBuilder.from_dataframe(dataframe)
    options_builder.configure_default_column(sortable=False)
    options_builder.configure_columns(editable_columns, editable=True)
    options_builder.configure_column(date_column, pinned=True, suppressSizeToFit=True, maxWidth=75)
    options_builder.configure_column('full_name', pinned=True, suppressSizeToFit=True)
    options_builder.configure_pagination(paginationAutoPageSize=False, paginationPageSize=10)
    options_builder.configure_side_bar()
    grid_options = options_builder.build()
    if st.session_state.user.groups.filter(name__in=["Check-in Team"]).exists(): # confirming that user is in checkin group
        grid_options['columnDefs'].append({"field": date_column, "header": "MarkAttendance", "pinned": True,
            "editable": False, "maxWidth":50, "cellRenderer": CheckinBtnCellRenderer, "cellRendererParams": {"color": "#FFC533","background_color": "black"}
        })
    else:
        grid_options['columnDefs'].append({"field": date_column, "header": "MarkAttendance", "pinned": True,
            "editable": False, "maxWidth":50, "cellRenderer": BtnCellRenderer, "cellRendererParams": {"color": "#FFC533","background_color": "black"}
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
    full_modified_df.loc[:,'date_added'] = pd.to_datetime(full_modified_df['date_added'], infer_datetime_format=True) # ensure date is in datetime format
    return interactive_table,full_modified_df

def recalc_att_ytd(dataframe, today): # select sundays on or before sundays
    date_list_column = [] # create list to store dates from date columns
    start_column = dataframe.columns.get_loc('_08_Jan_23') # select index of first date column
    while int(start_column) < dataframe.shape[1]: # store date columns into the list
        date_list_column.append(pd.to_datetime(dataframe.columns[start_column], format='_%d_%b_%y'))
        start_column = int(start_column) + 3
    for i in dataframe.index: # for every person in the table
        date_added = dataframe.loc[i,'date_added'] # select date added
        dates_available = [] # create list to store all dates in the table that are after when the user was added to the table and are on or before today
        for date in date_list_column: # for every date present in the original table
            if date >= date_added and date <= pd.to_datetime(today): # check if the date is on or after the user was added and on or before today
                column_name = date.strftime('_%d_%b_%y')
                dates_available.append(column_name) # store that date into a list
        sundays_by_today = dataframe.loc[i,dates_available] # create dataframe with only those date columns
        sundays_by_today.fillna('',inplace=True)
        all_count = sundays_by_today.count() # count total days
        try:
            present_count = sundays_by_today.value_counts()['Present'] # count days present
            dataframe.loc[i,'att_ytd'] = round((present_count/all_count*100),2) # recalculate att_ytd
        except: dataframe.loc[i,'att_ytd'] = 0.00
    return dataframe

def save_data_updates(dataframe,credentials,date_column,group_logs): # save the updates in a log table
    with st.spinner('Saving data...'):
        # insert log details columns
        dataframe.insert(0,'time_filled','')
        dataframe.insert(0,'user','')
        dataframe['time_filled'] = datetime.now()
        dataframe['user'] = st.session_state.user.username
        dataframe[f'checkin_location{date_column}'] = st.session_state.user.last_name
        dataframe['date_added'] = pd.to_datetime(dataframe['date_added']) # ensure date added column is in the correct datatype
        pandas_gbq.to_gbq(dataframe=dataframe, destination_table=group_logs, project_id='the-new-ikeja', 
          chunksize=None, api_method='load_csv', if_exists='append',credentials=credentials) # save data to database
        if st.session_state.user.groups.filter(name__in=["Check-in Team"]).exists(): # confirming that user is in checkin group
            success_placeholder = st.empty() # add success message in placeholder
            success_placeholder.success('Data saved!')
            time.sleep(1)
            success_placeholder.empty()

def update_db(credentials, gs_credentials, group_logs, filepath='gs://the_new_global_db/the_new_global.csv'): # update actual data table
    receiver = 'itunu.owo@gmail.com' # email recipient
    with st.spinner('Refreshing table..'):
        df_toupdate = pd.read_csv(filepath, storage_options={'token':'credentials.json'})
        query=f'SELECT * FROM {group_logs}'
        logs_df = pd.read_gbq(query, project_id='the-new-ikeja', credentials=credentials) # read logs
        logs_df = logs_df.sort_values('time_filled') # sort in ascending order by time of entry
        logs_df.drop(['user','time_filled'],axis=1,inplace=True) # drop user and time filled columns
        logs_df.drop_duplicates(['unique_id'],keep='last',inplace=True) # drop duplicate entries
        updated_df = pd.concat([df_toupdate,logs_df],axis=0,ignore_index=True) # append entries to original db
        updated_df.drop_duplicates(['unique_id'],keep='last',inplace=True) # drop duplicate entries
        try: # reconcile datetime formats
            updated_df.date_added = pd.to_datetime(updated_df.date_added, utc=True).dt.strftime('%Y-%m-%d')
        except: # send mail to self to reconcile dates
            subject = 'BigQuery and Google Sheets have done it again!'
            contents = """Reconcile 'date added' field values. Probably also check 'att_ytd' field too."""
            yag = yagmail.SMTP(user=sender, password='wtvkilvlkmfawnri')
            yag.send(to=receiver, subject=subject, contents=contents)
            pass
        updated_df.to_csv(filepath, storage_options={'token':'credentials.json'}, index=False) # save updates to original csv file
    with st.spinner('Updating Google Sheets...'):
        gc = gs.authorize(gs_credentials) # give gspread library access to the private google sheet
        gs_db = gc.open_by_url(st.secrets["private_gsheets_url"]) # open the spreadsheet
        db_to_update = gs_db.worksheet('database') # open the specific sheet to update
        updated_df.sort_values(by=['installation','SN'],inplace=True) # sort values
        updated_df.fillna('',inplace=True) # fill null values
        try: # update Google sheets
            db_to_update.update([updated_df.columns.values.tolist()] + updated_df.values.tolist(), value_input_option='USER_ENTERED')
        except: # send mail to self to check gsheet update
            subject = 'The New Global DB sheet was not updated!'
            contents = """Some updates were not parsed from BigQuery to Google Sheets"""
            yag = yagmail.SMTP(user=sender, password='wtvkilvlkmfawnri')
            yag.send(to=receiver, subject=subject, contents=contents)
            pass
        st.success('Updated!') # display success message
        time.sleep(1)

def arrange_dates(dataframe, data_columns, date_column, date_comment_column): # collate all date columns to one column for analysis purposes
    dates_list=[] # create list to store date columns
    data_columns.remove(date_column); data_columns.remove(date_comment_column) # remove date columns from data columns to keep only profile columns
    for column in dataframe.columns: # append dates to the list
        if column.startswith('_'): dates_list.append(column)
    needed_columns = data_columns+dates_list # store all columns in a variable
    unpivot_df = dataframe.loc[:,needed_columns] # select only the columns stored from the full database
    unpivot_df = pd.melt(unpivot_df, id_vars=data_columns, var_name='date', value_name='attendance') # create dataframe with dates in one column for analysis
    unpivot_df['attendance'] = unpivot_df['attendance'].replace('','Unknown')
    unpivot_df[f'checkin_location{date_column}'] = unpivot_df[f'checkin_location{date_column}'].replace('',np.nan)
    return unpivot_df

def presentcalc(dataframe): # calculate people present
    total_attendance = dataframe['attendance'].value_counts() # count total attendance
    if 'Present' in dataframe['attendance'].unique(): # if there are people present
        present_attendance = dataframe['attendance'].value_counts()['Present'] # count people present
        present_attendance_percent = round((dataframe['attendance'].value_counts(normalize=True)['Present']*100),2) # calculate % of people present
    else: # people present is zero
        present_attendance, present_attendance_percent = 0, 0.0
    return total_attendance, present_attendance, present_attendance_percent

def specific_date_summary_stats(dataframe,attendance_date,date_column,team_or_nation='service_team'): # calculate summary statistics for a specific date, you can group by team or nation
    dataframe['date'] = pd.to_datetime(dataframe['date'], format='_%d_%b_%y').dt.strftime('%Y-%m-%d') # put date column in corect format
    dataframe['att_ytd'] = dataframe['att_ytd'].replace(np.nan,0) # let all attendance percent values be numeric
    selected_day_df=dataframe[dataframe['date']==str(attendance_date)] # select data from the specified date
    if team_or_nation is None: team_or_nation_numbers = pd.DataFrame() # empty dataframe if not grouped by team or nation
    else: team_or_nation_numbers = selected_day_df[team_or_nation].value_counts().to_frame() # count of team or nation
    total_members = selected_day_df['full_name'].count() # total number of people in selected day
    last_week=attendance_date-timedelta(days=7) # check last week
    last_week_full_date = last_week.strftime('%A, %d %B %Y').strip() # write date in full for dashboard
    last_week_df=dataframe[dataframe['date']==str(last_week)].reset_index() # select data one week from the selected day
    todays_total_attendance, todays_present_attendance, todays_present_attendance_percent = presentcalc(selected_day_df) # calculate attendance of the selected day
    last_week_total_attendance, last_week_present_attendance, last_week_present_attendance_percent = presentcalc(last_week_df) # calculate attendance of the week before selected day
    if st.session_state.user.groups.filter(name__in=["Check-in Team"]).exists(): # confirming that user is in checkin group
        try: # select present checkin
            dataframe = dataframe[dataframe[f'checkin_location{date_column}'].str.contains('Check-in') &
                              (dataframe['attendance'] == 'Present')]
        except: pass
    return team_or_nation_numbers, total_members, last_week_full_date, todays_total_attendance, todays_present_attendance, todays_present_attendance_percent, last_week_total_attendance, last_week_present_attendance, last_week_present_attendance_percent,dataframe

def specific_date_dashboard(full_date, team_or_nation_numbers, total_members, todays_total_attendance, todays_present_attendance, todays_present_attendance_percent, last_week_full_date, last_week_present_attendance, head_type='total'): # create a dashboard of the summary statistics
    delta = int(todays_present_attendance-last_week_present_attendance) # calculate difference between specified date and week before attendance
    abs_delta = abs(delta) # store absolute value of difference
    relativity = '' # initialize a variable to store comparisons
    if todays_present_attendance_percent >= 70: st.balloons(); message = 'Congratulations!' # add congratulatory message if attendance is more than 70 percent
    else: message=''
    if team_or_nation_numbers.empty: pass
    else: 
        numbers_expander=st.expander(f'Are the {head_type}s under/over staffed or optimal?') # check numbers per group
        numbers_expander.dataframe(team_or_nation_numbers)   
    scorecard_column, tablechart_column, percent_columns = st.columns([1,1.25,1]) # create three different columns for dashboard
    # create scorecard chart
    scorecard_column.metric(label=f'Your {head_type} in church today', value=todays_present_attendance,
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
    percent_columns.markdown(f'''{message} <font style="color:#FFC533;font-size:20px;"><strong>{todays_present_attendance_percent}%</strong></font>   of your {head_type} members were in 
    church today.''', unsafe_allow_html=True)
    # create summary paragraph
    st.markdown(f'''###### Summary Paragraph:''')
    if delta>0: # specified date attendance more than last week attendance
        relativity = 'more than'; color=':green'
    elif delta<0: # specified date attendance less than last week attendance
        relativity = 'less than'; color=':red'
    else: # specified date attendance and previous week attendance are the same
        abs_delta=''; relativity = 'the same as'; color=':white'
    st.markdown(f'''In summary, you have **{total_members}** {head_type} members. 
    <font style="color:#FFC533">{todays_present_attendance}</font> of them came to church today and this is {abs_delta} {color}[{relativity} last week] {last_week_full_date}.
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
             .properties(width=180, height=90)).configure_header(titleColor='grey',titleFontSize=14,labelColor='#FFC533', labelFontSize=14)
    # create expanders for table and bar chart in separate columns
    facets_table = st.expander(f'View attendance table by: {title}')
    facets_table.write(facet_data)
    try:
        facets_chart = st.expander(f'View attendance charts by: {title}')
        facets_chart.altair_chart(chart)
    except: pass

def filtered_people_list(dataframe, full_date, date_column, type:str, cols:list): # filter dataframe for absent and unaccounted for people
    cols.append(date_column)
    df_subset = dataframe.loc[:,cols]  # select revelant columns
    if type.title()=='Unaccounted': # for unaccounted people
        st.write(f'People unaccounted for in church on {full_date}')
        df = df_subset[(df_subset[date_column] != 'Absent') & (df_subset[date_column] != 'Present')].reset_index(drop=True) # filter to people who have neither been recorded as present or absent
    elif type.title()=='Absent': # for absent people
        st.write(f'People {type.lower()} in church on {full_date}')
        df = df_subset[df_subset[date_column] == type.title()].reset_index(drop=True) # filter to people who have been marked absent
    st.dataframe(df) # show dataframe

def attendance_metric(dataframe,columns,att_percent_query): # select people with attendance of a certain percentage
    att = dataframe.query(att_percent_query) 
    att = att.loc[:,columns] # return specified columns
    return att

def timeseries_trends(dataframe, columns, facet_by='installation',tab_name='team'): # create a time series trends section
    # convert date column to datetime format
    try: dataframe['date'] = pd.to_datetime(dataframe['date'])
    except: dataframe['date'] = pd.to_datetime(dataframe['date'], format='_%d_%b_%y')
    individual_att_ytd = dataframe.drop(['date','attendance'], axis=1).drop_duplicates() # drop the date and attendance columns and select unique records
    poor_attendance = attendance_metric(individual_att_ytd, columns, att_percent_query='att_ytd < 50.00') # identify people with poor attendance
    good_attendance = attendance_metric(individual_att_ytd, columns, att_percent_query='att_ytd >= 70.00') # identify people with good attendance
    average_attendance = attendance_metric(individual_att_ytd, columns, att_percent_query='att_ytd >=50.00 & att_ytd<70.00') # identify people with average attendance
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
        filtered_linechart_data = filtered_dates.groupby(['date','attendance'])['full_name'].count().reset_index().query('attendance == "Present"') # group by date and attendance and select present attendance
        mean_att = round(filtered_linechart_data['full_name'].mean()) # calculate mean
        st.header(''); mean_column, trend_column = st.columns([1.5,4]) # create columns for mean and line chart
        mean_column.write(f'You have {len(individual_att_ytd)} people to account for.') # write how many people to account for
        mean_column.metric('Average attendance', value=mean_att, help='Average attendance over the selected timeframe') # write mean metric
        with trend_column: # create line chart
            chart = alt.Chart(filtered_linechart_data).mark_line(color='#FFC533')\
            .encode(x=alt.X('date:T', axis=alt.Axis(title=None)),
                    y=alt.Y('full_name', axis=alt.Axis(title='Attendees')),
                    tooltip=['date:T', 'full_name'])
            st.altair_chart(chart, use_container_width=True)
        if facet_by == 'full_name': faceted_linechart_data = filtered_dates.groupby(['date',facet_by,'attendance']).count().reset_index().query('attendance == "Present"') # aggregating by names
        else: # otherwise; also create faceted chart in an expander
            faceted_linechart_data = filtered_dates.groupby(['date',facet_by,'attendance'])['full_name'].count().reset_index().query('attendance == "Present"')
            faceted_linechart_data = faceted_linechart_data.pivot(index=facet_by,columns='date', values='full_name')
            faceted_linechart_data = faceted_linechart_data.replace(np.nan,0).reset_index()
            faceted_linechart_data = pd.melt(faceted_linechart_data, id_vars=[facet_by], var_name='date', value_name='full_name')
            title = str(facet_by).replace('_',' ').title()
            chart = (alt.Chart(faceted_linechart_data).mark_line(color='#FFC533')
                     .encode(x=alt.X('date:T', axis=alt.Axis(title=None)), 
                             y=alt.Y('full_name', axis=alt.Axis(title='Attendees')), 
                             tooltip=['date:T', 'full_name'], facet=alt.Facet(facet_by, columns=3, title=title))
                    .properties(width=180, height=90)).configure_header(titleColor='grey',
                                                                        titleFontSize=14, 
                                                                        labelColor='#FFC533',
                                                                        labelFontSize=14)
            chart_expander = st.expander(f'View trends by: {title}')
            chart=chart_expander.altair_chart(chart)
    with dedicated_tab: # for dedicated attendees
        st.success((f'You have {good_attendance.shape[0]} dedicated person/people'))
        # create table of count per group
        attendance_count = good_attendance[facet_by].value_counts().to_frame().reset_index().rename(columns={'index':f'{facet_by}', f'{facet_by}':'count'})
        st.dataframe(attendance_count)
    with inprogress_tab: # for average attendees
        st.warning(f'You have {average_attendance.shape[0]} person/people on the fence')
        # create table of count per group
        attendance_count = average_attendance[facet_by].value_counts().to_frame().reset_index().rename(columns={'index':f'{facet_by}', f'{facet_by}':'count'})
        st.dataframe(attendance_count)
    with icu_tab: # for poor attendees
        st.error(f'You have {poor_attendance.shape[0]} ICU patients')
        # create table of count per group
        attendance_count = poor_attendance[facet_by].value_counts().to_frame().reset_index().rename(columns={'index':f'{facet_by}', f'{facet_by}':'count'})
        st.dataframe(attendance_count)
    return dashboard_tab,dedicated_tab,inprogress_tab,icu_tab

def load_hall_counts(credentials,bqtable='hall_count.global_hall_count'): # load hall counts from db
    query=f'SELECT * FROM {bqtable}' # query bq table
    hall_count_df = pd.read_gbq(query, project_id='the-new-ikeja', credentials=credentials) # read table
    hall_count_df = hall_count_df.sort_values(['date','time_filled']) # sort in ascending order by time of entry
    hall_count_df.drop_duplicates(['date','installation'],keep='last',inplace=True) # drop duplicate entries
    return hall_count_df

def save_hall_counts(credentials,gs_credentials,values:list,bqtable='hall_count.global_hall_count'): # save hall count record to bq table
    body = dict(values=values) # store form values in a dictionary
    df = pd.DataFrame(body).transpose() # convert dict to DataFrame and transpose
    df.rename(columns={0:'date', 1:'installation',2:'hall_count_adults',
                       3:'hall_count_children'}, inplace=True) # rename columns as needed
    df.reset_index(drop=True,inplace=True) # reset index
    df['time_filled'] = datetime.now() # fill log time entry
    with st.spinner('Saving data...'):
        df.sort_values(by=['date','installation'],inplace=True) # sort values
        pandas_gbq.to_gbq(dataframe=df, destination_table=bqtable, project_id='the-new-ikeja', 
          chunksize=None, api_method='load_csv', if_exists='append',credentials=credentials) # save data to database
        gc = gs.authorize(gs_credentials) # give gspread library access to the private google sheet
        gs_db = gc.open_by_url(st.secrets["hall_counts_url"]) # open the spreadsheet
        df.fillna('',inplace=True) # fill null values
        df_gs = df.loc[:,['date','installation','hall_count_adults']]
        df_gs['date'] = pd.to_datetime(df_gs['date']).dt.strftime('%B %d, %Y')
        df_gs.rename(columns={'date':'Date','installation':'Installation','hall_count_adults':'Count'},inplace=True)
        hc_to_update = gs_db.worksheet('Hall Counts') # open the specific sheet to update
        hc_to_update.update([df_gs.columns.values.tolist()] + df_gs.values.tolist(), value_input_option='USER_ENTERED')
        success_placeholder = st.empty() # add success message in placeholder
        success_placeholder.success('Data saved!')
        time.sleep(1)
        success_placeholder.empty()

def save_checkin_firsttimers_notindb(dataframe, checkin_location, first_timers, not_in_db, credentials, bqtable='hall_count.for_variance_calc'): # save first timers and not in db numbers
    with st.spinner('Saving data...'):
        dataframe = dataframe[dataframe['installation'].eq(checkin_location)] # select relevant installation
        condition = [dataframe['installation'].eq(checkin_location)] # select checkin location
        ft_choice = [first_timers] # create array of first timers numbers
        nidb_choice = [not_in_db] # create array of not in db numbers
        dataframe['count_first_timers'] = np.select(condition, ft_choice, default=dataframe['count_first_timers']) # update first timers numbers in hall count dataframe
        dataframe['count_not_in_db'] = np.select(condition, nidb_choice, default=dataframe['count_not_in_db']) # update not in db numbers in hall count dataframe
        dataframe['time_filled'] = datetime.now() # input time filled
        dataframe['user'] = st.session_state.user.username #input user name
        pandas_gbq.to_gbq(dataframe=dataframe, destination_table=bqtable, project_id='the-new-ikeja', 
            chunksize=None, api_method='load_csv', if_exists='append',credentials=credentials) # save data to database
        st.success('Updated!')

def hall_count_variance(dataframe,attendance_date,credentials,group_by_column): # calculate checkin vs hall count variance
    dataframe = dataframe[dataframe[group_by_column].str.contains('Check-in') & (dataframe['attendance']=='Present')] # restrict to present from checkin
    dataframe = dataframe[dataframe['date']==str(attendance_date)] # select specified date from data table
    dataframe=dataframe.groupby(group_by_column).count()['attendance'].reset_index() # group by column selected to facet by and reset index
    dataframe.rename(columns={'attendance':'count'},inplace=True)# rename attendance column to count
    dataframe[['checkin','installation']] = dataframe[group_by_column].str.split(expand=True) # split checkin location column
    hall_counts = load_hall_counts(credentials,bqtable='hall_count.for_variance_calc') # load updated hallcount dataframe
    hall_counts['date'] = pd.to_datetime(hall_counts['date']).dt.strftime('%Y-%m-%d') # convert date column in hal count to string
    hall_counts = hall_counts[hall_counts['date']==str(attendance_date)] # filter to selected date
    dataframe = dataframe.merge(hall_counts, how='left', on='installation') # merge with hall counts
    dataframe['checkin_attendance'] = dataframe['count'] + dataframe['count_first_timers'] + dataframe['count_not_in_db'] # calc total checkin attendance
    variance = dataframe['hall_count_adults']-dataframe['checkin_attendance'] # calculate variance
    dataframe['percent_variance'] = round((variance/dataframe['hall_count_adults'])*100,2) # calculate percentage variance in 2 decimal places
    dataframe.rename(columns={'count':'count_in_db'},inplace=True) # rename count column
    dataframe = dataframe.iloc[:,[5,0,12,6,11,1,9,8]] # rearrange columns needed
    st.write(dataframe)

def modify_person_details(credentials, biodata_df, installation, df_for_modify, modify='service_team', action='addition'): # modify single person details
    modify_label = modify.replace('_',' ').title() # how to label what to modify
    search_id_col, id_col = st.columns([1,4])
    search_id = search_id_col.selectbox('Search group:', ['Full name','Email address','Phone number']) # select id to search by
    search_group = search_id.replace(' ','_').lower() # create field to search by converting search id to snake case
    search_list = list(biodata_df[search_group]) # create list of search results
    while '' in search_list: search_list.remove('') # remove blank results
    search_list.insert(0,'') # insert only one blank entry at the start of the search results
    id = id_col.selectbox(f"What is the person's {search_id.lower()}?", options=search_list) # ask for id
    bio_details = biodata_df[biodata_df[search_group]==id] # select details of that id
    bio_display = bio_details.set_index(search_group) # how to display details
    try: bio_installation = bio_display.loc[id,'installation'] # store person's installation in a variable
    except: pass
    # process for different table lengths
    if len(bio_details) == 0: pass
    if len(bio_details) > 1: st.warning(f'There are multiple entries with this {search_group}. Please pick another to uniquely identify this person')
    elif len(bio_details) == 1 and bio_installation != installation: # if record is unique but installation is different from user's installation
        st.warning(f'There is a record with this {search_id} but it is listed under another installation as shown below. Please liaise with the installation to rectify this')
        st.dataframe(bio_display)
    elif len(bio_details)==1 and bio_installation==installation: # if record is unique and installation is same as user's
        st.dataframe(bio_display)
        radio_col, value_col = st.columns([1,4])
        correct = radio_col.radio('This is the correct person.',['Yes','No'],horizontal=True) # ask if record is correct
        if correct=='No':value_col.write('Please search with another search group. If the record is still not found, contact your data team')
        else:
            options_to_choose = sorted(df_for_modify[df_for_modify[modify].notnull()][modify].unique()) # select distinct available options
            options_list = list(options_to_choose) # create list of available options
            # store update in data record
            if (action=='addition') or (action=='assignment') or (action=='transfer'): # for additions
                value = value_col.selectbox(f'Select {modify_label}', options=options_list) # select new team or nation
                bio_details[modify] = value # overwrite previous value
                if modify=='service_team': # for service teams, overwrite team head field
                    teams = df_for_modify[[modify,'team_head']].drop_duplicates()
                    team_head = teams[teams[modify]==value].iloc[0,1]
                    bio_details['team_head'] = team_head
            elif action=='deletion': # for deletions...
                bio_details[modify] = np.nan
                if modify=='service_team': bio_details['team_head'] = np.nan
                if modify=='nation': bio_details['nation_head'] = np.nan
            reason = value_col.text_area('Reason') # add reason
            bio_details['reason'] = reason # update reason
            bio_details['time_filled'] = datetime.now() # log time filled
            bio_details['user'] = st.session_state.user.username # log user
            if value_col.button('Request'): # to send request
                user_last_name = st.session_state.user.last_name
                table_name = user_last_name.replace(' ','_')
                with st.spinner('Sending request...'):
                    pandas_gbq.to_gbq(dataframe=bio_details, destination_table=f'data_requests.{table_name}_{action}', 
                                    project_id='the-new-ikeja', chunksize=None, api_method='load_csv', if_exists='append',credentials=credentials) # save data to database
                with st.spinner('Sending mail...'):
                    receiver = 'itunu.owo@gmail.com'
                    cc = [st.session_state.user.email, 'adetowun.adekoya@gmail.com', 'kelechianyasol@gmail.com']
                    subject = f'{modify_label} {action.title()}'
                    contents = f"""Dear Data Team, {st.session_state.user.first_name}, {user_last_name}, has logged a request for single {action}. Please action within 4 days.
                    \n@{st.session_state.user.email}, please note that records without both phone numbers and email addresses will not be actioned until updated and may take longer.
                    \nBest regards,\nThe New Data Ops."""
                    yag = yagmail.SMTP(user=sender, password='wtvkilvlkmfawnri')
                    yag.send(to=receiver, cc=cc, subject=subject, contents=contents)
                st.cache_data.clear()
                st.success(f'Request for {action} has been logged successfully')           

def modify_people_details(credentials, installation_biodata_df, options_df, modify='service_team', action='addition'): # modify multiple people details
    modify_label = modify.replace('_',' ').title() # how to label what to modify
    search_id_col, id_col = st.columns([1,4])
    search_id = search_id_col.selectbox('Search group:', ['Full name','Email address','Phone number'],key='multisearch') # select id to search by
    search_group = search_id.replace(' ','_').lower() # create field to search by converting search id to snake case
    search_list = list(installation_biodata_df[search_group]) # create list of search results
    while '' in search_list: search_list.remove('') # remove blank results
    search_list.insert(0,'') # insert only one blank entry at the start of the search results
    ids = id_col.multiselect(f"What are their {search_id.lower()}s?", options=search_list) # ask for id
    selected_ids = pd.DataFrame(ids,columns=[search_group]) # put selection in dataframe
    df_download = installation_biodata_df.merge(selected_ids, how='inner', on=search_group) # select biodata of selected people
    if df_download.empty is False: st.dataframe(df_download.set_index(search_group)) # see data to confirm these are the people whose details to modify
    options_to_choose = sorted(options_df[options_df[modify].notnull()][modify].unique()) # select distinct available options
    options_list = list(options_to_choose) # create list of available options to use as data validation
    buffer = BytesIO() # create bytesio file to store as excel
    writer  = pd.ExcelWriter(buffer, engine='xlsxwriter') # write excel file with xlsxwriter
    df_download.to_excel(writer, sheet_name=action, engine='xlsxwriter', index=False) # write sheet with data to download
    workbook, worksheet = writer.book, writer.sheets[action] # store workbook and worksheet in variable
    locked = workbook.add_format(); locked.set_locked(True) # set lock format for workbook
    unlocked = workbook.add_format(); unlocked.set_locked(False) # set unlock format for workbook
    worksheet.protect() # protect workbook
    worksheet.write('H1','reason', locked) # create new row for reason
    worksheet.set_column(0, 7, 25) # increase column width for all non-empty columns
    if modify == 'nation_head':
        worksheet.set_column('F2:F', None, unlocked)
        worksheet.data_validation('F2:F10000', {'validate':'list', 'source':options_list})
    elif modify == 'installation':
        worksheet.set_column('B2:B', None, unlocked)
        worksheet.data_validation('B2:B10000', {'validate':'list', 'source':options_list})
    else:
        worksheet.set_column('E2:E', None, unlocked) # unlock column with field to modify
        worksheet.data_validation('E2:E10000', {'validate': 'list', 'source': options_list}) # input the data validation list
    worksheet.set_column('H2:H', None, unlocked) # unlock reason column
    writer.close() # save file
    st.markdown(f'Download this table and fill the **_{modify_label} and reason columns_** only. Changes to other columns may cause an error during re-upload.')
    st.download_button(label="Download list as XLSX", data=buffer, file_name=f'{modify}_{action}.xlsx',
                       mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet') # download file
    st.write('Upload the updated file. It is advisable to upload the updated downloaded file. If you are uploading a file different from the one previously downloaded, ensure that the data types and structure match.Else, upload may fail.')
    uploaded_file = st.file_uploader('Upload the updated Excel file') # upload file
    if uploaded_file is not None: # when there is an upload
        try:
            df_upload = pd.read_excel(uploaded_file, dtype={'phone_number':'object'}) # read uploaded file
            for column in list(df_upload.columns): # fill null cells in columns that are not datetime or float
                df_upload[column].fillna('',inplace=True)
            drop_modify_df = installation_biodata_df.drop([modify],axis=1) # remove column in both dfs
            cols_to_merge = list(df_upload.columns) # create list of columns to merge by
            cols_to_merge.remove(modify); cols_to_merge.remove('reason')
            people_details = drop_modify_df.merge(df_upload, how='inner', on=cols_to_merge) # merge biodata df with uploaded df
            people_details['time_filled'] = datetime.now() # log time filled
            people_details['user'] = st.session_state.user.username # log user
            if (action=='addition') or (action=='assignment') or (action=='transfer'): # for additions
                if modify=='service_team': # if service teams, update team head field also
                    teams = installation_biodata_df[[modify,'team_head']].drop_duplicates()
                    people_details.drop('team_head',axis=1,inplace=True)
                    people_details = people_details.merge(teams, how='left', on=modify)
                elif modify=='nation':
                    people_details['nation_head'] = np.nan
            if action=='deletion': # clear field if delete
                people_details[modify] = np.nan
                if modify=='service_team': people_details['team_head'] = np.nan
                if modify=='nation': people_details['nation_head'] = np.nan
            if st.button('Request', key='multirqst'): # to save request
                user_last_name = st.session_state.user.last_name # store user last name in a variable
                table_name = user_last_name.replace(' ','_') # store table name in a variable
                with st.spinner('Sending request...'):
                    pandas_gbq.to_gbq(dataframe=people_details, destination_table=f'data_requests.{table_name}_{action}', 
                                    project_id='the-new-ikeja', chunksize=None, api_method='load_csv', if_exists='append',credentials=credentials) # save data to database
                with st.spinner('Sending mail...'):
                    receiver = 'itunu.owo@gmail.com'
                    cc = [st.session_state.user.email, 'adetowun.adekoya@gmail.com', 'kelechianyasol@gmail.com']
                    subject = f'{modify_label} {action.title()}'
                    contents = f"""Dear Data Team, {st.session_state.user.first_name}, {user_last_name}, has logged a request for multiple {action}. Please action within 4 days.
                    \n@{st.session_state.user.email}, please note that records without both phone numbers and email addresses will not be actioned until updated and may take longer.
                    \nBest regards,\nThe New Data Ops."""
                    yag = yagmail.SMTP(user=sender, password='wtvkilvlkmfawnri') # initialize mail activity
                    yag.send(to=receiver, cc=cc, subject=subject, contents=contents) # send mail
                st.cache_data.clear()
                st.success(f'Request for {action} has been logged successfully')
        except: st.error('An error occured!'); st.stop()

def change_head(credentials, installation_biodata_df, modify='service_team', head='team_head'): # change service team or nation head
    modify_label = modify.replace('_',' ').title() # how to label what to modify
    head_label = head.replace('_',' ').title() # how to label what to modify
    full_list_names = list(installation_biodata_df['full_name']) # create list of full name
    teams = installation_biodata_df[[modify,head]].drop_duplicates() # create df of service teams/nation and the respective heads
    teams_list = list(teams[modify].drop_duplicates()) # create list of teams
    team_heads_list = list(teams[head]) # create list of current team heads
    while '' in full_list_names: full_list_names.remove('') # remove all blanks in the list
    while '' in teams_list: teams_list.remove('') # remove all blanks in the list
    while '' in team_heads_list: team_heads_list.remove('') # remove all blanks in the list
    full_list_names.insert(0,'') # add only one blank to the start of the list
    col1, col2, col3 = st.columns(3) # create three columns
    team_value = col1.selectbox(f'Select the {modify_label}',teams_list) # team to change
    if modify=='service_team':
        team_head = teams[teams[modify]==team_value].iloc[0,1]
        current_team_head = col2.text_input(f'Current {head_label}', team_head, disabled=True) # current team head
    elif modify=='nation':
        team_head = teams[teams[modify]==team_value].iloc[:,1]
        current_team_head = col2.selectbox(f'Current {head_label}', team_head) # current team head
    new_team_head = col3.selectbox('Select the new head', full_list_names) # select new head
    head_change = pd.DataFrame()
    head_change.loc[0,['team','current_team_head','new_team_head']] = team_value, current_team_head, new_team_head
    submit = st.button('Request') # to save request
    if submit:
        user_last_name = st.session_state.user.last_name # store user last name in a variable
        table_name = user_last_name.replace(' ','_') # store table name in a variable
        with st.spinner('Sending request...'):
            pandas_gbq.to_gbq(dataframe=head_change, destination_table=f'data_requests.{table_name}_change_{head}', 
                              project_id='the-new-ikeja', chunksize=None, api_method='load_csv', if_exists='append',credentials=credentials) # save data to database
        with st.spinner('Sending mail...'):
            receiver = 'itunu.owo@gmail.com'
            cc = [st.session_state.user.email, 'adetowun.adekoya@gmail.com', 'kelechianyasol@gmail.com']
            subject = f'{modify_label} Change {head_label}'
            contents = f"""Dear Data Team, {st.session_state.user.first_name}, {user_last_name}, has logged a request for  change of {head_label}. Please action within 4 days.
            \nBest regards,\nThe New Data Ops."""
            yag = yagmail.SMTP(user=sender, password='wtvkilvlkmfawnri') # initialize mail activity
            yag.send(to=receiver, cc=cc, subject=subject, contents=contents) # send mail
            st.cache_data.clear()
            st.success(f'Change request has been logged successfully')

def modify_single_installation_details(credentials, biodata_df, installation, df_for_modify, modify='installation', action='addition'): # modify single person's installation
    modify_label = modify.replace('_',' ').title() # how to label what to modify
    search_id_col, id_col = st.columns([1,4])
    search_id = search_id_col.selectbox('Search group:', ['Full name','Email address','Phone number']) # select id to search by
    search_group = search_id.replace(' ','_').lower() # create field to search by converting search id to snake case
    search_list = list(biodata_df[search_group]) # create list of search results
    while '' in search_list: search_list.remove('') # remove blank results
    search_list.insert(0,'') # insert only one blank entry at the start of the search results
    id = id_col.selectbox(f"What is the person's {search_id.lower()}?", options=search_list) # ask for id
    bio_details = biodata_df[biodata_df[search_group]==id] # select details of that id
    bio_display = bio_details.set_index(search_group) # how to display details
    try: bio_installation = bio_display.loc[id,'installation'] # store person's installation in a variable
    except: pass
    # process for different table lengths
    if len(bio_details) == 0: pass
    if len(bio_details) > 1: st.warning(f'There are multiple entries with this {search_group}. Please pick another to uniquely identify this person')
    elif len(bio_details) == 1 and bio_installation == installation: # if record is unique but installation is different from user's installation
        st.warning(f'There is a record with this {search_id} but it is already listed under your installation')
        st.dataframe(bio_display)
    elif len(bio_details)==1 and bio_installation!=installation: # if record is unique and installation is same as user's
        st.dataframe(bio_display)
        radio_col, value_col = st.columns([1,4])
        correct = radio_col.radio('This is the correct person.',['Yes','No'],horizontal=True) # ask if record is correct
        if correct=='No':value_col.write('Please search with another search group. If the record is still not found, contact your data team')
        else:
            options_to_choose = sorted(df_for_modify[df_for_modify[modify].notnull()][modify].unique()) # select distinct available options
            options_list = list(options_to_choose) # create list of available options
            # store update in data record
            if (action=='addition'): # for additions
                value = value_col.selectbox(f'Select {modify_label}', options=options_list) # select new team or nation
                bio_details[modify] = value # overwrite previous value
            elif action=='deletion': # for deletions...
                bio_details[modify] = np.nan
            reason = value_col.text_area('Reason') # add reason
            bio_details['reason'] = reason # update reason
            bio_details['time_filled'] = datetime.now() # log time filled
            bio_details['user'] = st.session_state.user.username # log user
            if value_col.button('Request'): # to send request
                user_last_name = st.session_state.user.last_name
                table_name = user_last_name.replace(' ','_')
                with st.spinner('Sending request...'):
                    pandas_gbq.to_gbq(dataframe=bio_details, destination_table=f'data_requests.{table_name}_{action}', 
                                    project_id='the-new-ikeja', chunksize=None, api_method='load_csv', if_exists='append',credentials=credentials) # save data to database
                with st.spinner('Sending mail...'):
                    receiver = 'itunu.owo@gmail.com'
                    cc = [st.session_state.user.email, 'kelechianyasol@gmail.com']
                    subject = f'{modify_label} {action.title()}'
                    contents = f"""Dear Data Team, {st.session_state.user.first_name}, {user_last_name}, has logged a request for single {action}. Please action within 4 days.
                    \n@{st.session_state.user.email}, please note that records without both phone numbers and email addresses will not be actioned until updated and may take longer.
                    \nBest regards,\nThe New Data Ops."""
                    yag = yagmail.SMTP(user=sender, password='wtvkilvlkmfawnri')
                    yag.send(to=receiver, cc=cc, subject=subject, contents=contents)
                st.cache_data.clear()
                st.success(f'Request for {action} has been logged successfully')           

