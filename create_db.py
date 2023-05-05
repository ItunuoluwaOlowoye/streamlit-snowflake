import streamlit as st
import pandas as pd
from snowflake.connector.pandas_tools import write_pandas
from snowflake.connector import connect

df = pd.read_csv('employee_data.csv')
df.fillna('',inplace=True)
df.date_hired = pd.to_datetime(df.date_hired, utc=True)
df.SN = df.SN.astype(int)
df.att_ytd = df.att_ytd.astype(float)
df.phone_number = df.phone_number.astype('str')
st.write(df.dtypes)
st.write(df)

connection = st.experimental_connection('snowflake', type='sql')

cnx = connect(user='Itee', password='Itunu@snowflake23', account='qgrnfkj-mj51774', 
              database='EMPLOYEE_DATA', schema='PUBLIC', warehouse='COMPUTE_WH', role='ACCOUNTADMIN')

if st.button('Create table?'):
    # Write the data from the DataFrame to the table named "employees".
    success, nchunks, nrows, _ = write_pandas(conn=cnx, df=df, table_name='employees', database='EMPLOYEE_DATA', schema='PUBLIC', auto_create_table=True, overwrite=True)

    st.success('Table created')