import pandas as pd
import streamlit as st

from availability import get_availability

st.title('Vaccine Availability')
st.markdown('Contribute on [GitHub](https://github.com/bhavsarpratik/vaccine_availability)')

next_n_days = 3

data = pd.read_csv('districts.csv')
mapper = dict(data.values)
avail_districts = list(mapper.keys())

min_age_limit = st.sidebar.selectbox('Min age limit', [18, 45])
option = st.sidebar.multiselect('How would you like to be contacted?', avail_districts, "Ahmedabad Corporation")

district_ids = [mapper[val] for val in option]

try:
    df = get_availability(next_n_days, district_ids, min_age_limit)
    df.index += 1
    st.table(df)
except:
    st.markdown('Unable to fetch data. Try after a few minutes')
