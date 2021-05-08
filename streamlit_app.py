import pandas as pd
import streamlit as st
import pgeocode
from availability import get_availability
import math
from st_download_button import download_button

@st.cache
def cached_availability(district_ids, min_age_limit, pincode_search, free_paid, show_empty_slots):
    df= get_availability(district_ids, min_age_limit, pincode_search, show_empty_slots)
    if len(df)>0:
        df = df[df['Free/Paid'].isin(free_paid)]
    return df

@st.cache
def get_district_info():
    data = pd.read_csv('districts.csv')
    mapper = {}
    for index, row in data.iterrows():
        mapper[row['district_name']] = row['district_id']
    return mapper


def main():
    mapper = get_district_info()
    avail_districts = list(mapper.keys())
    min_age_limit = st.sidebar.number_input('Age', min_value=18, max_value=100, value=35)
    # next_n_days = st.sidebar.number_input('Search next N Days', value=3, min_value=1, max_value=100)
    # next_n_days = 1
    districts = st.sidebar.multiselect('Select the District', avail_districts, "Ahmedabad Corporation")
    district_ids = [mapper[val] for val in districts]
    pincode_search = st.sidebar.text_input(label='Search Near your Pincode', value="")
    free_paid = st.sidebar.multiselect(label="Free or Paid", options=["Free", "Paid"], default=["Free", "Paid"])
    show_empty_slots = st.sidebar.checkbox(label="Show Full Slots?", value=False)

    st.title('Vaccine Availability')
    st.markdown('Contribute on [GitHub](https://github.com/bhavsarpratik/vaccine_availability)')
    pincode_msg = f"Pincode {pincode_search} not recognized. Will show all results of the district"
    pincode_success = False
    if pincode_search != "":
        nomi = pgeocode.Nominatim('in')
        if not math.isnan(nomi.query_postal_code(str(pincode_search)).latitude):
            pincode_msg = f"Pincode {pincode_search} found. Will show closest results to you"
            pincode_success = True
        else:
            pincode_search = ""
    if pincode_success:
        st.success(pincode_msg)
    else:
        st.warning(pincode_msg)
    search = st.button("Search")
    if search:
        df = cached_availability(district_ids, min_age_limit, pincode_search, free_paid, show_empty_slots)
        if len(df)>0:
            # df = get_availability(next_n_days, district_ids, min_age_limit)
            idx_cols = ['Center','District', 'Free/Paid','Min Eligible Age', 'Pin Code']
            if "Distance from you(km)" in df.columns:
                idx_cols += ['Distance from you(km)']
            df = pd.pivot_table(df, index=idx_cols, columns=['date'], values=['Available Slots']).fillna(0).reset_index()
            if "Distance from you(km)" in df.columns:
                df.sort_values(["Distance from you(km)"], ascending=[True], inplace=True)
            else:
                df.sort_values(['Center'], ascending=[True], inplace=True)
            st.dataframe(df)
            download_button_str = download_button(
                df,
                "upcoming_slots.csv",
                f"Click here to download slots as csv",
                pickle_it=False,
            )
            st.markdown(download_button_str, unsafe_allow_html=True)
        else:
            st.subheader("No available slots in any of the centers.")


if __name__ == "__main__":
    main()