#!/usr/bin/env python3
""" Pi Garage Alert

Author: Richard L. Lynch <rich@richlynch.com>

Description: Emails, tweets, or sends an SMS if a garage door is left open
too long.

Learn more at http://www.richlynch.com/code/pi_garage_alert
"""

##############################################################################
#
# The MIT License (MIT)
#
# Copyright (c) 2013-2014 Richard L. Lynch <rich@richlynch.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
#
##############################################################################

import time
from time import strftime
import subprocess
import re
import sys
import json
import logging
from datetime import timedelta
import smtplib
import traceback
from email.mime.text import MIMEText

import datetime
import pytz

from astral import LocationInfo
from astral.sun import sun

from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

import requests
import tweepy
import RPi.GPIO as GPIO
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import slack

sys.path.append('/usr/local/etc')
import pi_garage_alert_config as cfg


##############################################################################
# Twilio support
##############################################################################

class Twilio:
    """Class to connect to and send SMS using Twilio"""

    def __init__(self):
        self.twilio_client = None
        self.logger = logging.getLogger(__name__)

    def send_sms(self, recipient, msg):
        """Sends SMS message to specified phone number using Twilio.

        Args:
            recipient: Phone number to send SMS to.
            msg: Message to send. Long messages will automatically be truncated.
        """

        # User may not have configured twilio - don't initialize it until it's
        # first used
        if self.twilio_client is None:
            self.logger.info("Initializing Twilio")

            if cfg.TWILIO_ACCOUNT == '' or cfg.TWILIO_TOKEN == '':
                self.logger.error("Twilio account or token not specified - unable to send SMS!")
            else:
                self.twilio_client = Client(cfg.TWILIO_ACCOUNT, cfg.TWILIO_TOKEN)

        if self.twilio_client is not None:
            self.logger.info("Sending SMS to %s: %s", recipient, msg)
            try:
                self.twilio_client.messages.create(
                    to=recipient,
                    from_=cfg.TWILIO_PHONE_NUMBER,
                    body=truncate(msg, 140))
            except TwilioRestException as ex:
                self.logger.error("Unable to send SMS: %s", ex)
            except Exception as ex:
                self.logger.error("Exception sending SMS: %s %s", ex, sys.exc_info()[0])

##############################################################################
# Twitter support
##############################################################################

class Twitter:
    """Class to connect to and send DMs/update status on Twitter"""

    def __init__(self):
        self.twitter_api = None
        self.logger = logging.getLogger(__name__)

    def connect(self):
        """Initialize Twitter API object.

        Args:
            None
        """

        # User may not have configured twitter - don't initialize it until it's
        # first used
        if self.twitter_api is None:
            self.logger.info("Initializing Twitter")

            if cfg.TWITTER_CONSUMER_KEY == '' or cfg.TWITTER_CONSUMER_SECRET == '':
                self.logger.error("Twitter consumer key/secret not specified - unable to Tweet!")
            elif cfg.TWITTER_ACCESS_KEY == '' or cfg.TWITTER_ACCESS_SECRET == '':
                self.logger.error("Twitter access key/secret not specified - unable to Tweet!")
            else:
                auth = tweepy.OAuthHandler(cfg.TWITTER_CONSUMER_KEY, cfg.TWITTER_CONSUMER_SECRET)
                auth.set_access_token(cfg.TWITTER_ACCESS_KEY, cfg.TWITTER_ACCESS_SECRET)
                self.twitter_api = tweepy.API(auth)

    def direct_msg(self, user, msg):
        """Send direct message to specified Twitter user.

        Args:
            user: User to send DM to.
            msg: Message to send. Long messages will automatically be truncated.
        """

        self.connect()

        if self.twitter_api is not None:
            # Twitter doesn't like the same msg sent over and over, so add a timestamp
            msg = strftime("%Y-%m-%d %H:%M:%S: ") + msg

            self.logger.info("Sending twitter DM to %s: %s", user, msg)
            try:
                self.twitter_api.send_direct_message(recipient_id=user, text=truncate(msg, 140))
            except tweepy.error.TweepError as ex:
                self.logger.error("Unable to send Tweet: %s", ex)

    def update_status(self, msg):
        """Update the users's status

        Args:
            msg: New status to set. Long messages will automatically be truncated.
        """

        self.connect()

        if self.twitter_api is not None:
            # Twitter doesn't like the same msg sent over and over, so add a timestamp
            msg = strftime("%Y-%m-%d %H:%M:%S: ") + msg

            self.logger.info("Updating Twitter status to: %s", msg)
            try:
                self.twitter_api.update_status(status=truncate(msg, 140))
            except tweepy.error.TweepError as ex:
                self.logger.error("Unable to update Twitter status: %s", ex)

##############################################################################
# Email support
##############################################################################

class Email:
    """Class to send emails"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def send_email(self, recipient, subject, msg):
        """Sends an email to the specified email address.

        Args:
            recipient: Email address to send to.
            subject: Email subject.
            msg: Body of email to send.
        """
        self.logger.info("Sending email to %s: subject = \"%s\", message = \"%s\"", recipient, subject, msg)

        msg = MIMEText(msg)
        msg['Subject'] = subject
        msg['To'] = recipient
        msg['From'] = cfg.EMAIL_FROM
        msg['X-Priority'] = cfg.EMAIL_PRIORITY

        try:
            mail = smtplib.SMTP(cfg.SMTP_SERVER, cfg.SMTP_PORT)
            if cfg.SMTP_USER != '' and cfg.SMTP_PASS != '':
                mail.login(cfg.SMTP_USER, cfg.SMTP_PASS)
            mail.sendmail(cfg.EMAIL_FROM, recipient, msg.as_string())
            mail.quit()
        except:
            self.logger.error("Exception sending email: %s", sys.exc_info()[0])

##############################################################################
# Pushbullet support
##############################################################################

class Pushbullet:
    """Class to send Pushbullet notes"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def send_note(self, access_token, title, body):
        """Sends a note to the specified access token.

        Args:
            access_token: Access token of the Pushbullet account to send to.
            title: Note title
            body: Body of the note to send
        """
        self.logger.info("Sending Pushbullet note to %s: title = \"%s\", body = \"%s\"", access_token, title, body)

        headers = {'Content-type': 'application/json'}
        payload = {'type': 'note', 'title': title, 'body': body}

        try:
            session = requests.Session()
            session.auth = (access_token, "")
            session.headers.update(headers)
            session.post("https://api.pushbullet.com/v2/pushes", data=json.dumps(payload))
        except:
            self.logger.error("Exception sending note: %s", sys.exc_info()[0])

##############################################################################
# IFTTT support using Maker Channel (https://ifttt.com/maker)
##############################################################################

class IFTTT:
    """Class to send IFTTT triggers using the Maker Channel"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def send_trigger(self, event, value1, value2, value3):
        """Send an IFTTT event using the maker channel.

        Get the key by following the URL at https://ifttt.com/services/maker/settings

        Args:
            event: Event name
            value1, value2, value3: Optional data to supply to IFTTT.
        """
        self.logger.info("Sending IFTTT event \"%s\": value1 = \"%s\", value2 = \"%s\", value3 = \"%s\"", event, value1, value2, value3)

        headers = {'Content-type': 'application/json'}
        payload = {'value1': value1, 'value2': value2, 'value3': value3}
        try:
            requests.post("https://maker.ifttt.com/trigger/%s/with/key/%s" % (event, cfg.IFTTT_KEY), headers=headers, data=json.dumps(payload))
        except:
            self.logger.error("Exception sending IFTTT event: %s", sys.exc_info()[0])

##############################################################################
# Google Cloud Messaging support
##############################################################################

class GoogleCloudMessaging:
    """Class to send GCM notifications"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def send_push(self, state, body):
        """Sends a push notification to the specified topic.

        Args:
            state: Garage door state as string ("0"|"1")
            body: Body of the note to send
        """
        status = "1" if state == 'open' else "0"

        self.logger.info("Sending GCM push to %s: status = \"%s\", body = \"%s\"", cfg.GCM_TOPIC, status, body)

        auth_header = "key=" + cfg.GCM_KEY
        headers = {'Content-type': 'application/json', 'Authorization': auth_header}
        payload = {'to': cfg.GCM_TOPIC, 'data': {'message': body, 'status': status}}

        try:
            session = requests.Session()
            session.headers.update(headers)
            session.post("https://gcm-http.googleapis.com/gcm/send", data=json.dumps(payload))
        except:
            self.logger.error("Exception sending push: %s", sys.exc_info()[0])

##############################################################################
# Slack support
##############################################################################
class Slack:
    """ Class to send a slack message to the configured channel using
    the configured BOT
        Requires a Slack API token

        Requires installation of the python slack client
            > Install via pip using:
                pip install slackclient
            > Or see github page for details:
                http://slackapi.github.io/python-slackclient/
    """

    def __init__(self):
        if cfg.SLACK_BOT_TOKEN:
            self.slack_client = slack.WebClient(cfg.SLACK_BOT_TOKEN)
        else:
            self.slack_client = None
        self.logger = logging.getLogger(__name__)

    def send_message(self, channel, state, body):
        """
            Args:
            channel: Channel ID to send to
            state: Garage door state as string
            body: Body of the note to send
        """
        if self.slack_client:
            self.logger.info("Sending Slack Message: state = \"%s\", body = \"%s\"", state, body)
            try:
                self.slack_client.api_call("chat.postMessage", json={'channel': channel, 'text': body})
            except:
                self.logger.error("Exception sending slack message: %s", sys.exc_info()[0])
        else:
            self.logger.error('Slack bot token not configured - unable to send message to Slack channel')

##############################################################################
# Sensor support
##############################################################################

def get_garage_door_state(pin):
    """Returns the state of the garage door on the specified pin as a string

    Args:
        pin: GPIO pin number.
    """
    if GPIO.input(pin): # pylint: disable=no-member
        state = 'open'
    else:
        state = 'closed'

    return state

def get_uptime():
    """Returns the uptime of the RPi as a string
    """
    with open('/proc/uptime', 'r') as uptime_file:
        uptime_seconds = int(float(uptime_file.readline().split()[0]))
        uptime_string = str(timedelta(seconds=uptime_seconds))
    return uptime_string

def get_gpu_temp():
    """Return the GPU temperature as a Celsius float
    """
    cmd = ['vcgencmd', 'measure_temp']

    measure_temp_proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
    output = measure_temp_proc.communicate()[0]

    gpu_temp = 'unknown'
    gpu_search = re.search('([0-9.]+)', output)

    if gpu_search:
        gpu_temp = gpu_search.group(1)

    return float(gpu_temp)

def get_cpu_temp():
    """Return the CPU temperature as a Celsius float
    """
    cpu_temp = 'unknown'
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as temp_file:
        cpu_temp = float(temp_file.read()) / 1000.0

    return cpu_temp

def rpi_status():
    """Return string summarizing RPi status
    """
    return "CPU temp: %.1f, GPU temp: %.1f, Uptime: %s" % (get_gpu_temp(), get_cpu_temp(), get_uptime())

##############################################################################
# Logging and alerts
##############################################################################

def send_alerts(logger, alert_senders, recipients, subject, msg, state, time_in_state):
    """Send subject and msg to specified recipients

    Args:
        recipients: An array of strings of the form type:address
        subject: Subject of the alert
        msg: Body of the alert
        state: The state of the door
    """
    for recipient in recipients:
        if recipient[:6] == 'email:':
            alert_senders['Email'].send_email(recipient[6:], subject, msg)
        elif recipient[:11] == 'twitter_dm:':
            alert_senders['Twitter'].direct_msg(recipient[11:], msg)
        elif recipient == 'tweet':
            alert_senders['Twitter'].update_status(msg)
        elif recipient[:4] == 'sms:':
            alert_senders['Twilio'].send_sms(recipient[4:], msg)
        elif recipient[:11] == 'pushbullet:':
            alert_senders['Pushbullet'].send_note(recipient[11:], subject, msg)
        elif recipient[:6] == 'ifttt:':
            alert_senders['IFTTT'].send_trigger(recipient[6:], subject, state, '%d' % (time_in_state))
        elif recipient == 'gcm':
            alert_senders['Gcm'].send_push(state, msg)
        elif recipient[:6] == 'slack:':
            alert_senders['Slack'].send_message(recipient[6:], state, msg)
        else:
            logger.error("Unrecognized recipient type: %s", recipient)

##############################################################################
# Misc support
##############################################################################

def truncate(input_str, length):
    """Truncate string to specified length

    Args:
        input_str: String to truncate
        length: Maximum length of output string
    """
    if len(input_str) < (length - 3):
        return input_str

    return input_str[:(length - 3)] + '...'

def format_duration(duration_sec):
    """Format a duration into a human friendly string"""
    days, remainder = divmod(duration_sec, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    ret = ''
    if days > 1:
        ret += "%d days " % (days)
    elif days == 1:
        ret += "%d day " % (days)

    if hours > 1:
        ret += "%d hours " % (hours)
    elif hours == 1:
        ret += "%d hour " % (hours)

    if minutes > 1:
        ret += "%d minutes" % (minutes)
    if minutes == 1:
        ret += "%d minute" % (minutes)

    if ret == '':
        ret += "%d seconds" % (seconds)

    return ret


##############################################################################
# Main functionality
##############################################################################
class PiGarageAlert:
    """Class with main function of Pi Garage Alert"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def main(self):
        """Main functionality
        """

        try:
            # Set up logging
            log_fmt = '%(asctime)-15s %(levelname)-8s %(message)s'
            log_level = logging.INFO

            if sys.stdout.isatty():
                # Connected to a real terminal - log to stdout
                logging.basicConfig(format=log_fmt, level=log_level)
            else:
                # Background mode - log to file
                logging.basicConfig(format=log_fmt, level=log_level, filename=cfg.LOG_FILENAME)

            # Banner
            self.logger.info("==========================================================")
            self.logger.info("Pi Garage Alert starting")

            # Use Raspberry Pi board pin numbers
            self.logger.info("Configuring global settings")
            GPIO.setmode(GPIO.BOARD)

            # Configure the sensor pins as inputs with pull up resistors
            for door in cfg.GARAGE_DOORS:
                self.logger.info("Configuring pin %d for \"%s\"", door['pin'], door['name'])
                GPIO.setup(door['pin'], GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Last state of each garage door
            door_states = dict()

            # time.time() of the last time the garage door changed state
            time_of_last_state_change = dict()

            # Index of the next alert to send for each garage door
            alert_states = dict()

            # Create alert sending objects
            alert_senders = {
                "Twitter": Twitter(),
                "Twilio": Twilio(),
                "Email": Email(),
                "Pushbullet": Pushbullet(),
                "IFTTT": IFTTT(),
                "Gcm": GoogleCloudMessaging(),
                "Slack": Slack()
            }

            # Get location information
            self.logger.info(f"Getting location info for lat: {cfg.LOC_LATITUDE}, lon: {cfg.LOC_LONGITUDE}")
            geolocator = Nominatim(user_agent="pi_garage_alert")
            location = geolocator.reverse((cfg.LOC_LATITUDE, cfg.LOC_LONGITUDE), exactly_one=True)

            address = location.raw.get('address', {})
            city = address.get('city') or address.get('town') or address.get('village')
            country = address.get('country')

            tf = TimezoneFinder()
            timezone_str = tf.timezone_at(lat=cfg.LOC_LATITUDE, lng=cfg.LOC_LONGITUDE)
            timezone = pytz.timezone(timezone_str)
            self.logger.info(f"Retrieved location info, city: {city}, country: {country}, timezone: {timezone_str}")          

            # Read initial states
            for door in cfg.GARAGE_DOORS:
                name = door['name']
                state = get_garage_door_state(door['pin'])

                door_states[name] = state
                time_of_last_state_change[name] = time.time()
                alert_states[name] = 0

                self.logger.info("Initial state of \"%s\" is %s", name, state)

            status_report_countdown = 5
            while True:
                for door in cfg.GARAGE_DOORS:
                    name = door['name']
                    state = get_garage_door_state(door['pin'])
                    time_in_state = time.time() - time_of_last_state_change[name]
                    local_now = datetime.datetime.now().astimezone(timezone)
                    city_loc_info = LocationInfo(city, country, timezone_str, cfg.LOC_LATITUDE, cfg.LOC_LONGITUDE)
                    local_dusk = sun(city_loc_info.observer, date=local_now)['dusk']
                    after_dusk = local_now > local_dusk


                    # Check if the door has changed state
                    if door_states[name] != state:
                        door_states[name] = state
                        time_of_last_state_change[name] = time.time()
                        self.logger.info("State of \"%s\" changed to %s after %.0f sec", name, state, time_in_state)

                        # Reset alert when door changes state
                        if alert_states[name] > 0:
                            # Use the recipients of the last alert
                            recipients = door['alerts'][alert_states[name] - 1]['recipients']
                            send_alerts(self.logger, alert_senders, recipients, name, "%s is now %s" % (name, state), state, 0)
                            alert_states[name] = 0

                        # Reset time_in_state
                        time_in_state = 0

                    # See if there are more alerts
                    if len(door['alerts']) > alert_states[name]:
                        # Get info about alert
                        alert = door['alerts'][alert_states[name]]

                        # Has the time elapsed and is this the state to trigger the alert?
                        if time_in_state > alert['time'] and state == alert['state'] and after_dusk:
                            send_alerts(self.logger, alert_senders, alert['recipients'], name, "%s has been %s for %d seconds!" % (name, state, time_in_state), state, time_in_state)
                            alert_states[name] += 1

                # Periodically log the status for debug and ensuring RPi doesn't get too hot
                status_report_countdown -= 1
                if status_report_countdown <= 0:
                    status_msg = rpi_status()

                    for name in door_states:
                        status_msg += ", %s: %s/%d/%d" % (name, door_states[name], alert_states[name], (time.time() - time_of_last_state_change[name]))

                    self.logger.info(status_msg)

                    status_report_countdown = 600

                # Poll every 1 second
                time.sleep(1)
        except KeyboardInterrupt:
            logging.critical("Terminating due to keyboard interrupt")
        except:
            logging.critical("Terminating due to unexpected error: %s", sys.exc_info()[0])
            logging.critical("%s", traceback.format_exc())

        GPIO.cleanup() # pylint: disable=no-member

if __name__ == "__main__":
    PiGarageAlert().main()
