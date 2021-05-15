import datetime
import json
import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List
from collections import defaultdict

import cachetools.func
import pandas as pd
import requests
from retry import retry

headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}


def get_all_district_ids():
    district_df_all = None
    for state_code in range(1, 40):
        response = requests.get("https://cdn-api.co-vin.in/api/v2/admin/location/districts/{}".format(state_code), timeout=3, headers=headers)
        district_df = pd.DataFrame(json.loads(response.text))
        district_df = pd.json_normalize(district_df['districts'])
        if district_df_all is None:
            district_df_all = district_df
        else:
            district_df_all = pd.concat([district_df_all, district_df])

        district_df_all.district_id = district_df_all.district_id.astype(int)

    district_df_all = district_df_all[["district_name", "district_id"]].sort_values("district_name")
    return district_df_all

@cachetools.func.ttl_cache(maxsize=100, ttl=30 * 60)
@retry(KeyError, tries=5, delay=2)
def get_data(URL):
    response = requests.get(URL, timeout=3, headers=headers)
    data = json.loads(response.text)['centers']
    return data

def getDetails(district_id, age_limit):
    d = defaultdict(list)
    data = requests.get("https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={}&date=05-05-2021".format(district_id)).json()

    for i in range(len(data['centers'])):
        for j in range(len(data['centers'][i]['sessions'])):
            if data['centers'][i]['sessions'][j]['available_capacity'] > 0 and data['centers'][i]['sessions'][j]['min_age_limit'] == age_limit:
                d['center_id'].append(data['centers'][i]['center_id'])
                d['center_name'].append(data['centers'][i]['name'])
                d['center_address'].append(data['centers'][i]['address'])
                d['district_name'].append(data['centers'][i]['district_name'])
                d['pincode'].append(data['centers'][i]['pincode'])
                d['available vaccines'].append(data['centers'][i]['sessions'][j]['available_capacity'])            

    if len(d) == 0 or d == None:
        msg = "Vaccine currently unavaible for {}+ age limit. Please try after some time".format(age_limit)
        return msg

    df = pd.DataFrame(d)    

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
    dist_ids = [Ahmedabad, Ahmedabad_Corporation]
    min_age_limit = 18

    availability_data = get_availability(dist_ids, min_age_limit)
    send_email(availability_data, min_age_limit)
