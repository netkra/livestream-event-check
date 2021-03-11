import requests
import json
import smtplib, ssl
import datetime
from datetime import timedelta
import os
from os import path

# Install configparser (for Python 3.x)
# $ pip3 install configparser
try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser  # ver. < 3.0

# instantate
config = ConfigParser()
configFilePath = 'vimeo.py.conf'
config.read(configFilePath)

# import config variables
api_key = config.get('main', 'api_key').replace('"', '')
account_id = config.get('main', 'account_id').replace('"', '')
live_event_id = config.get('main', 'live_event_id').replace('"', '')
sender_name = config.get('email', 'sender_name').replace('"', '')
sender_email = config.get('email', 'sender_email').replace('"', '')
alert_lock_file = config.get('email', 'alert_lock_file').replace('"', '')
smtps_server = config.get('email', 'smtps_server').replace('"', '')
smtps_port = config.get('email', 'smtps_port')
smtps_user = config.get('email', 'smtps_user').replace('"', '')
smtps_pwd = config.get('email', 'smtps_pwd').replace('"', '')
event_desc = config.get('email', 'event_desc').replace('"', '')
event_url = config.get('email', 'event_url').replace('"', '')
receivers = config.get('email', 'receivers').replace('"', '')

API_URL = 'https://livestreamapis.com/v3/accounts/'


def send_mail(time_now):
    header = "From: " + sender_name + " <" + sender_email + ">" + "\n"
    header += "To: " + sender_name + "<" + sender_email + ">" + "\n"
    subject = "Subject: " + event_desc + " is NOT live (" + time_now + ")\n\n"
    message = event_desc + " event (#" + live_event_id + ") is not live.\n\n"
    message += "Link: " + event_url + "\n\n"
    message += "Alert sent on " + time_now + " CET.\n"
    mail_data = header + subject + message

    receivers_list = receivers.split(",")

    # Create a secure SSL context
    context = ssl.create_default_context()
    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(smtps_server, smtps_port)
        server.ehlo() # Can be omitted
        server.starttls(context=context) # Secure the connection
        server.login(smtps_user, smtps_pwd)
        server.ehlo() # Can be omitted
        server.sendmail(sender_email, receivers_list, mail_data)
    except Exception as e:
        # Print any error messages to stdout
        print(e)
    finally:
        server.quit()


def main():
    api_event_url = API_URL + account_id + "/events/" + live_event_id
    datetime_obj_now = datetime.datetime.now() + timedelta(hours=2)
    now = datetime_obj_now.strftime('%d-%m-%Y %H:%M:%S')
    hour = int(datetime_obj_now.strftime('%H'))
    minute = int(datetime_obj_now.strftime('%M'))
    if (hour > 1 and hour < 23) or (hour == 23 and minute < 45) or (hour == 1 and minute > 15):
        r = requests.get(api_event_url, auth=(api_key,''))
        if r.status_code == 200:
            j = json.loads(r.text)
            if j['isLive'] is False:
                # if alert_file exists, an e-mail has been sent
                if path.exists("./" + alert_lock_file):
                    with open("./" + alert_lock_file,'r+') as f:
                        datetime_obj_f = datetime.datetime.strptime(f.read(), '%d-%m-%Y %H:%M:%S')
                        datetime_obj_f += timedelta(minutes=30)
                        if datetime_obj_now > datetime_obj_f:
                            send_mail(now)
                            f.write(now)

                    f.close()
                # no e-mail has been sent yet
                else:
                    send_mail(now)
                    with open("./" + alert_lock_file,'w') as f:
                        f.write(now)
                    f.close()
            else:
                if path.exists("./" + alert_lock_file):
                    os.remove("./" + alert_lock_file)
        else:
            pass


if __name__ == "__main__":
    main()
