import datetime
import json
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Optional

import cachetools.func
import pandas as pd
import requests
from retry import retry
import pgeocode


def get_all_district_ids():
    district_df_all = None
    for state_code in range(1, 40):
        response = requests.get("https://cdn-api.co-vin.in/api/v2/admin/location/districts/{}".format(state_code), timeout=3)
        district_df = pd.DataFrame(json.loads(response.text))
        district_df = pd.json_normalize(district_df['districts'])
        if district_df_all is None:
            district_df_all = district_df
        else:
            district_df_all = pd.concat([district_df_all, district_df])

        district_df_all.district_id = district_df_all.district_id.astype(int)

    district_df_all = district_df_all[["district_name", "district_id"]].sort_values("district_name")
    return district_df_all

@cachetools.func.ttl_cache(maxsize=100, ttl=10 * 60)
@retry(KeyError, tries=5, delay=2)
def get_data(URL):
    response = requests.get(URL, timeout=3)
    data = json.loads(response.text)['centers']
    return data

def get_availability(days: int, district_ids: List[int], min_age_limit: int, pincode_search: Optional[str] = None):
    base = datetime.datetime.today()
    date_list = [base + datetime.timedelta(days=x) for x in range(days)]
    date_str = [x.strftime("%d-%m-%Y") for x in date_list]
    INP_DATE = date_str[-1]

    all_date_df = []

    for district_id in district_ids:
        print(f"checking for INP_DATE:{INP_DATE} & DIST_ID:{district_id}")
        URL = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={}&date={}".format(district_id, INP_DATE)
        data = get_data(URL)
        df = pd.DataFrame(data)
        if len(df):
            df = df.explode("sessions")
            df['min_age_limit'] = df.sessions.apply(lambda x: x['min_age_limit'])
            df['available_capacity'] = df.sessions.apply(lambda x: x['available_capacity']).astype(int)
            df['date'] = df.sessions.apply(lambda x: x['date'])
            df['vaccine'] = df.sessions.apply(lambda x: x['vaccine'])
            df = df[["date", "min_age_limit", "available_capacity", "pincode", "name", "state_name", "district_name", "block_name", "fee_type", "vaccine"]]
            all_date_df.append(df)
            # if all_date_df is not None:
            #     all_date_df = pd.concat([all_date_df, df])
            # else:
            #     all_date_df = df
    if len(all_date_df)>0:
        all_date_df = pd.concat(all_date_df)
        all_date_df = all_date_df.drop(["block_name"], axis=1)
        if pincode_search is not None and pincode_search!="":
            dist = pgeocode.GeoDistance('in')
            all_date_df['distance'] = df.pincode.apply(lambda x: dist.query_postal_code(str(pincode_search), x)).fillna(9999).round(0)
            all_date_df.sort_values(["distance", "available_capacity"], ascending=[True, False], inplace=True)
        else:
            all_date_df.sort_values(["available_capacity"], ascending=[False], inplace=True)
        all_date_df = all_date_df[all_date_df.min_age_limit <= min_age_limit]
        all_date_df = all_date_df[all_date_df.available_capacity > 0]
        # Human Readable Column names
        all_date_df.rename(columns={
            "name": "Center",
            "district_name": "District",
            "fee_type": "Free/Paid",
            "min_age_limit": "Min Eligible Age",
            "pincode": "Pin Code",
            "distance": "Distance from you(km)",
            "available_capacity": "Available Slots"
        }, inplace=True)
        return all_date_df
    return pd.DataFrame()


def send_email(data_frame, age):
    # Used most of code from https://realpython.com/python-send-email/ and modified

    sender_email = os.environ['SENDER_EMAIL']
    receiver_email = os.environ['RECEIVER_EMAIL']
    message = MIMEMultipart("alternative")
    message["From"] = sender_email
    message["To"] = receiver_email
    if data_frame is None or len(data_frame.index) == 0:
        print("Empty Data")
        message["Subject"] = "Availability for Max Age {} is 0 <EOM>".format(age, len(data_frame.index))
        text = ""
        part1 = MIMEText(text, "plain")
        message.attach(part1)

    else:

        message["Subject"] = "Availability for Max Age {} Count {}".format(age, len(data_frame.index))
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
    tvm = 296
    kannur = 297
    dist_ids = [tvm]
    next_n_days = 1
    min_age_limit = 40

    availability_data = get_availability(next_n_days, dist_ids, min_age_limit)
    print(availability_data)
    send_email(availability_data, min_age_limit)
