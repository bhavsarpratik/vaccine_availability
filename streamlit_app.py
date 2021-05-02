import pandas as pd
import streamlit as st

from availability import get_availability

st.title('Vaccine Availability')
st.markdown('<-- Select district in the left side bar')
st.markdown('Contribute on [GitHub](https://github.com/bhavsarpratik/vaccine_availability)')

@st.cache
def get_data():
    return pd.read_csv('districts.csv')

data = get_data()

mapper = dict(data.values)
avail_districts = list(mapper.keys())
min_age_limit = st.sidebar.radio('Min age limit', [18, 45])
option = st.sidebar.multiselect('District', avail_districts, "Ahmedabad Corporation")

district_ids = [mapper[val] for val in option]

try:
    df = get_availability(district_ids, min_age_limit)
    df.index += 1
    st.table(df)
except:
    st.error('Unable to fetch data. Try after a few minutes')
