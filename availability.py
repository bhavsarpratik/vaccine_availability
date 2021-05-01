import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List

import requests
import datetime

import json
import pandas as pd


def get_all_district_ids():
    district_df_all = None
    for state_code in range(1, 40):
        response = requests.get("https://cdn-api.co-vin.in/api/v2/admin/location/districts/{}".format(state_code))
        district_df = pd.DataFrame(json.loads(response.text))
        district_df = pd.json_normalize(district_df['districts'])
        if district_df_all is None:
            district_df_all = district_df
        else:
            district_df_all = pd.concat([district_df_all, district_df])

        district_df_all.district_id = district_df_all.district_id.astype(int)

    district_df_all = district_df_all[["district_name", "district_id"]].sort_values("district_name")
    return district_df_all


def get_availability(days: int, district_ids: List[int]):
    base = datetime.datetime.today()
    date_list = [base + datetime.timedelta(days=x) for x in range(days)]
    date_str = [x.strftime("%d-%m-%Y") for x in date_list]

    all_date_df = None
    df = None
    for INP_DATE in date_str:
        for DIST_ID in district_ids:
            print(f"checking for INP_DATE:{INP_DATE} & DIST_ID:{DIST_ID}")
            try:
                URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={}&date={}".format(
                    DIST_ID, INP_DATE)
                response = requests.get(URL)
                data = json.loads(response.text)['centers']
                df = pd.DataFrame(data)
                df['min_age_limit'] = df.sessions.apply(lambda x: [{d["date"]: d['min_age_limit']} for d in x])
                df = df.explode("min_age_limit")
                df["date"] = df['min_age_limit'].apply(lambda x: list(x.keys())[0])
                df["min_age_limit"] = df['min_age_limit'].apply(lambda x: list(x.values())[0])
                df = df[
                    ["date", "min_age_limit", "name", "state_name", "district_name", "block_name", "pincode", "fee_type"]]
                if all_date_df is not None:
                    all_date_df = pd.concat([all_date_df, df])
                else:
                    all_date_df = df
            except Exception as ex:
                print("Getting error in fetching data " + ex)

    if df is not None:
        df.drop(["block_name"], axis=1)
    return df


def send_email(data_frame, age):
    # Used most of code from https://realpython.com/python-send-email/ and modified
    if data_frame is None or len(data_frame.index) == 0:
        print("Empty Data")
        return

    sender_email = os.environ['SENDER_EMAIL']
    receiver_email = os.environ['RECEIVER_EMAIL']

    message = MIMEMultipart("alternative")
    message["Subject"] = "Availability for Max Age {} Count {}".format(age, len(data_frame.index))
    message["From"] = sender_email
    message["To"] = receiver_email

    text = """\
    Hi,
    Please refer vaccine availability"""

    html_header = """\
    <html>
      <body>
        <p>

    """

    html_footer = """\
    
        </p>
      </body>
    </html>
    """

    html = "{}{}{}".format(html_header, data_frame.to_html(), html_footer)

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    message.attach(part1)
    message.attach(part2)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, os.environ['SENDER_PASSWORD'])
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )


if __name__ == "__main__":
    Ahmedabad = 154
    Ahmedabad_Corporation = 770
    DIST_IDS = [Ahmedabad, Ahmedabad_Corporation]
    next_n_days = 5
    max_age_criteria = 100

    availability_data = get_availability(next_n_days, DIST_IDS)
    if availability_data is not None:
        availability_data = availability_data[availability_data.min_age_limit < max_age_criteria]

    send_email(availability_data, max_age_criteria)
