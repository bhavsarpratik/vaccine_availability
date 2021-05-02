# Vaccine Availability With Python
Get vaccine availability in India

## [Streamlit app](https://share.streamlit.io/bhavsarpratik/vaccine_availability/main)  
![Mail](.github/streamlit.png?raw=true")  

## CRON job for mail
Script runs every 6 hours. You can change this [here](https://github.com/bhavsarpratik/vaccine_availability/blob/main/.github/workflows/cron.yaml#L8)  

Steps
- Fork the code
- Enable [less secure apps](https://myaccount.google.com/lesssecureapps)
- Set up 2-factor authentication, and then generating an app-specific password with these [instructions](https://support.google.com/domains/answer/9437157)
- Add [these](https://github.com/bhavsarpratik/vaccine_availability/blob/main/.github/workflows/cron.yaml#L32) secrets to repo settings. Use the app specific password generated above
- Get district id from [here](https://github.com/bhavsarpratik/vaccine_availability/blob/main/districts.csv)
- Change config in your [code](https://github.com/bhavsarpratik/vaccine_availability/blob/main/availability.py#L119)


## Mail preview  
![Mail](.github/mail.png?raw=true")
