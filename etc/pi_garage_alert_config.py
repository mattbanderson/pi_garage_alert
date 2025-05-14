#!/usr/bin/env python3

##############################################################################
# Global settings
##############################################################################

# Describes all the garage doors being monitored
GARAGE_DOORS = [
#    {
#        'pin': 16,
#        'name': "Garage Door 1",
#        'alerts': [
#            {
#                'state': 'open',
#                'time': 120,
#                'recipients': [ 'sms:+11112223333', 'sms:+14445556666' ]
#            },
#            {
#                'state': 'open',
#                'time': 600,
#                'recipients': [ 'sms:+11112223333', 'sms:+14445556666' ]
#            }
#        ]
#    },

    {
        'pin': 15,
        'name': "Example Garage Door",
        'alerts': [
#            {
#                'state': 'open',
#                'time': 120,
#                'recipients': [ 'sms:+11112223333', 'email:someone@example.com', 'twitter_dm:twitter_user', 'pushbullet:access_token', 'gcm', 'tweet', 'ifttt:garage_door' ]
#            },
#            {
#                'state': 'open',
#                'time': 600,
#                'recipients': [ 'sms:+11112223333', 'email:someone@example.com', 'twitter_dm:twitter_user', 'pushbullet:access_token', 'gcm', 'tweet', 'ifttt:garage_door' ]
#            }
        ]
    }
]

# All messages will be logged to stdout and this file
LOG_FILENAME = "/var/log/pi_garage_alert.log"

##############################################################################
# Location settings
##############################################################################
LOC_LATITUDE = 40.7128
LOC_LONGITUDE = -74.0060

##############################################################################
# Email settings
##############################################################################

SMTP_SERVER = 'localhost'
SMTP_PORT = 25
SMTP_USER = ''
SMTP_PASS = ''
EMAIL_FROM = 'Garage Door <user@example.com>'
EMAIL_PRIORITY = '1'
# 1 High, 3 Normal, 5 Low

##############################################################################
# Azure Communication Services Email settings
##############################################################################

ACS_FROM = 'DoNotReply@example.com'
ACS_CONN_STR = ''

##############################################################################
# Twitter settings
##############################################################################

# Follow the instructions on http://talkfast.org/2010/05/31/twitter-from-the-command-line-in-python-using-oauth/
# to obtain the necessary keys

TWITTER_CONSUMER_KEY = ''
TWITTER_CONSUMER_SECRET = ''
TWITTER_ACCESS_KEY = ''
TWITTER_ACCESS_SECRET = ''

##############################################################################
# Twilio settings
##############################################################################

# Sign up for a Twilio account at https://www.twilio.com/
# then these will be listed at the top of your Twilio dashboard

TWILIO_ACCOUNT = ''
TWILIO_TOKEN = ''

# SMS will be sent from this phone number
TWILIO_PHONE_NUMBER = '+11234567890'

##############################################################################
# Google Cloud Messaging settings
##############################################################################

GCM_KEY = ''
GCM_TOPIC = ''

##############################################################################
# IFTTT Maker Channel settings
# Create an applet using the "Maker" channel, pick a event name,
# and use the event name as a recipient of one of the alerts,
# e.g. 'recipients': [ 'ifft:garage_event' ]
#
# Get the key by going to https://ifttt.com/services/maker/settings.
# The key is the part of the URL after https://maker.ifttt.com/use/.
# Do not include https://maker.ifttt.com/use/ in IFTTT_KEY.
##############################################################################

IFTTT_KEY = ''

##############################################################################
# Slack settings
# Send messages to a team slack channel
# e.g. 'recipients': [ 'slack:<your channel ID>']
#   where <your channel ID> is the name or ID of the slack channel you want to
#   send to
#
# To use this functionality you will need to create a bot user to do the posting
# For information on how to create the bot user and get your API token go to:
#   https://api.slack.com/bot-users
#
# Note that the bot user must be added to the channel you want to post
# notifications in
##############################################################################
SLACK_BOT_TOKEN = ''
