import streamlit as st
from sqlalchemy import create_engine
import pandas as pd
snowflake_username = 'Itee'
snowflake_password = 'Adenike@16'
snowflake_account = 'qgrnfkj-mj51774'
snowflake_warehouse = 'COMPUTE_WH'
snowflake_database = 'EMPLOYEE_DATA'
snowflake_schema = 'PUBLIC'

df_sensor = pd.read_csv('employee_data.csv')

connection = st.experimental_connection('snowflake', type='sql')

import pandas
from snowflake.connector.pandas_tools import pd_writer

df_sensor.to_sql('employees', con=connection, schema='PUBLIC', index=False, method=pd_writer)
results = connection.execute('select count(1) from tb_equipments').fetchone()
st.write(results[0])