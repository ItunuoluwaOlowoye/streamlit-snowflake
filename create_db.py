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

try:
    df_sensor.columns = map(str.upper, df_sensor.columns)
    df_sensor.to_sql('tb_equipments'.lower(), con=connection, 
    schema='public', index=False, if_exists='append', chunksize=16000)
    results = connection.execute('select count(1) from tb_equipments').fetchone()
    st.write(results[0])

finally: 
    connection.close()