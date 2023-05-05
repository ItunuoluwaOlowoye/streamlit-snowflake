import streamlit as st
import pandas as pd
from snowflake.connector.pandas_tools import write_pandas
from snowflake.connector import connect

df_sensor = pd.read_csv('employee_data.csv')

connection = st.experimental_connection('snowflake', type='sql')

cnx = connect(user='Itee', password='Adenike@16', account='qgrnfkj-mj51774', 
              database='EMPLOYEE_DATA', schema='PUBLIC', warehouse='COMPUTE_WH', role='ACCOUNTADMIN')

# Write the data from the DataFrame to the table named "employees".
success, nchunks, nrows, _ = write_pandas(conn=cnx, df=df_sensor, table_name='employees', database='EMPLOYEE_DATA', schema='PUBLIC', auto_create_table=True, overwrite=True)
st.success('success!')