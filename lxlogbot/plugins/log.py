from mongoengine import *

from rtmbot.core import Plugin
from datetime import datetime

import db

class LogPlugin(Plugin):
    def __init__(self, slack_client, plugin_config):
        Plugin.__init__(self, slack_client, plugin_config)
        connect("lxlogbot")
        print("Messages recieved:", len(db.Message.objects()))
    def process_message(self, data):
        user = data['user']
        ts = data['ts']
        channel = data['channel']
        text = data['text']
        db.Message(u=user, t=datetime.fromtimestamp(int(float(ts))), c=channel, x=text).save()
