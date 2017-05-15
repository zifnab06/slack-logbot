from mongoengine import *

class Message(Document):
    u = StringField() #user
    t = DateTimeField() #time
    c = StringField() #channel
    x = StringField() #text

class Channel(Document):
    cid = StringField() #channel id
    cn = StringField() #channel name

class User(Document):
    uid = StringField() #userid
    un = StringField() #username

    @classmethod
    def get_name(cls, uid):
        u = cls.objects(uid=uid).first()
        if u:
            return u.un
        else:
            return uid
    
