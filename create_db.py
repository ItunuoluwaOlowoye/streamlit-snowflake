import streamlit as st
import pandas as pd
from snowflake.connector.pandas_tools import write_pandas
from snowflake.connector import connect

df = pd.read_csv('employee_data.csv',dtype=str)
df.fillna('',inplace=True)
df.date_hired = pd.to_datetime(df.date_hired, utc=True).dt.strftime('%Y-%m-%d')
df.date_hired = pd.to_datetime(df.date_hired)
df.SN = df.SN.astype(int)
df.att_ytd = df.att_ytd.astype(float)

connection = st.experimental_connection('snowflake', type='sql')

cnx = connect(user='Itee', password='Itunu@snowflake23', account='qgrnfkj-mj51774', 
              database='EMPLOYEE_DATA', schema='PUBLIC', warehouse='COMPUTE_WH', role='ACCOUNTADMIN')

# Write the data from the DataFrame to the table named "employees".
success, nchunks, nrows, _ = write_pandas(conn=cnx, df=df, table_name='employees', database='EMPLOYEE_DATA', schema='PUBLIC', auto_create_table=True, overwrite=True)

st.write(success)