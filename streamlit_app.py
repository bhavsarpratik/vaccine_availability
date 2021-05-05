import pandas as pd
import streamlit as st
from availability import getDetails
import base64

st.title('Vaccine Availability')
st.markdown('Contribute on [GitHub](https://github.com/bhavsarpratik/vaccine_availability)')

@st.cache
def get_data():
    return pd.read_csv('districts.csv')

def get_table_download_link(df):
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(
        csv.encode()
    ).decode()
    
    return f'<a href="data:file/csv;base64,{b64}" download="vaccineData.csv">Download availabile vaccine table in the form of csv</a>'    

data = get_data()

age_limit = st.radio('Select',["18-44","45+"])
age_limit_ = int()
if age_limit == "18-44":
    age_limit_ = 18
else:
    age_limit_ = 45

district_name = st.selectbox(label='',options=data['district_name'].values)

district_id = data[data['district_name'] == district_name]['district_id'].values[0]

df = getDetails(district_id, age_limit_)

if isinstance(df, pd.DataFrame):
	st.markdown(get_table_download_link(df), unsafe_allow_html=True)
	st.table(df)
else:
    st.error(df)         




