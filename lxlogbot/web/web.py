from mongoengine import *
from slackclient import SlackClient

import db
import re
import html
from functools import wraps

from datetime import datetime, date, timedelta as td
from flask import Flask, abort, render_template, session, url_for, request, jsonify, redirect, request, make_response
from flask_cache import Cache
from flask.ext.github import GitHub

app = Flask(__name__)
app.config.from_pyfile("app.cfg")
connect("lxlogbot")
cache = Cache(app, config={'CACHE_TYPE': 'simple', 'CACHE_DEFAULT_TIMEOUT': 3600})
github = GitHub(app)
sc = SlackClient(app.config['SLACK_TOKEN'])

@app.cli.command()
def update_cache():
    """Updates username/channel cache"""

    #Get unique channel list
    for c in db.Message.objects().distinct('c'):
        if not db.Channel.objects(cid=c):
            chan = sc.api_call('channels.info', channel=c)
            if 'ok' in chan and chan['ok']:
                print('adding', chan['channel']['name'])
                db.Channel(cid=c, cn=chan['channel']['name']).save()
    #Get unique user list
    for u in db.Message.objects().distinct('u'):
        if not db.User.objects(uid=u):
            user = sc.api_call('users.info', user=u)
            if user.get('ok', False):
                print('adding', user['user']['name'])
                db.User(uid=u, un=user['user']['name']).save()


def require_login(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if 'github_token' not in session or not session['github_token']:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrapper

@app.route('/login/authorized')
@github.authorized_handler
def authorized(access_token):
    next_url = request.args.get('next') or url_for('main')
    if access_token is None:
        return redirect(next_url)
    print("foobar")
    print(access_token)
    req = github.raw_request("GET", "user/orgs", access_token=access_token)
    if req.status_code == 200:
        orgs = [x['login'] for x in req.json()]
    if app.config['GITHUB_ORG'] in orgs:
        session['github_token'] = access_token
        return redirect(next_url)
    else:
        return 'Invalid org, {} not in [{}]'.format(app.config['GITHUB_ORG'], ', '.join(orgs))

@app.route("/login", methods=['GET', 'POST'])
def login():
    if 'github_token' not in session or not session['github_token']:
        return github.authorize(scope="user:email, read:org")
    else:
        return redirect(url_for('main'))
        if result.user:
            result.user.update()
    return response

@app.route('/logout')
def logout():
    session.pop('github_token', None)
    return redirect(url_for('main'))

@github.access_token_getter
def get_github_oauth_token():
    return session.get('github_token')



@app.route("/")
@require_login
@cache.cached()
def main():
    channels = sorted([x.cn for x in db.Channel.objects()])
    print(channels)
    return render_template("index.html", channels=channels)

@app.route('/favicon.ico')
def favicon():
  return ''

@app.route("/<string:channel>/")
@require_login
@cache.cached()
def channel(channel):
    c = db.Channel.objects(cn=channel).first()
    if not c:
        abort(404)
    channel = c.cid
    first_message = db.Message.objects(c=channel).order_by('t').first().t.date()
    last_message = db.Message.objects(c=channel).order_by('-t').first().t.date()
    dates = [first_message + td(days=x) for x in range((last_message-first_message).days + 1)]
    
    return render_template("channel.html", dates=dates)


@app.route("/<string:channel>/<string:day>")
@require_login
@cache.cached()
def channel_by_date(channel, day):
    c = db.Channel.objects(cn=channel).first()
    if not c:
        abort(404)
    channel = c.cid
    start = datetime.strptime(day, "%Y-%m-%d")
    end = start + td(days=1)
    messages = []
    regex = re.compile(r'<@(U.*)>')
    for message in db.Message.objects(c=channel, t__lt=end, t__gt=start):
        text = html.unescape(message.x)
        match = re.search(regex, text)
        if match:
            for item in match.groups():
                print ('replacing', item, 'with', db.User.get_name(item))
                text = text.replace(item, db.User.get_name(item))
        messages.append("{} <{}> {}".format(message.t, db.User.get_name(message.u), text))
    return render_template("date.html", messages=messages)
