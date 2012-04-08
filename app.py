# DataShare
#
# share data view between multiple users
#
# when person visits site assign them a uuid
# data updates happen in the following manners
# - add new row
# - update specific cell

import json
import uuid

from flask import Flask, render_template, redirect, url_for, request
from gevent import queue
from gevent.pywsgi import WSGIServer

app = Flask(__name__)
app.debug = True

class DataSample(object):
    """Data wrapper"""
    def __init__(self):
        self.users = set()
        self.data = [
            {'first': 'Joe', 'last': 'Bloggs', 'd1': 10, 'd2': 20, 'd3': 30},
            {'first': 'Bill', 'last': 'Lewis', 'd1': 12, 'd2': 17, 'd3': 34},
            {'first': 'Jack', 'last': 'Higgins', 'd1': 15, 'd2': 42, 'd3': 3},
        ]

    def add(self, data):
        new_data = {
            'first': data.get('first', ''),
            'last': data.get('last', ''),
            'd1': data.get('d1', 0),
            'd2': data.get('d2', 0),
            'd3': data.get('d3', 0),
        }
        self.data.append(new_data)
        for user in self.users:
            user.queue.put_nowait(json.dumps({
                'action': 'add',
                'row': len(self.data),
                'data': new_data
            }))

    def update(self, key, field, value):
        row = self.data[int(key)]
        row[field] = value
        for user in self.users:
            user.queue.put_nowait(json.dumps({
                'action': 'update',
                'row': key,
                'field': field,
                'data': value
            }))

    def subscribe(self, user):
        self.users.add(user)

class User(object):
    def __init__(self):
        self.queue = queue.Queue()

users = {}
sample = DataSample()

@app.route("/")
def home():
    # set uuid for user
    # and forward to data page
    uid = uuid.uuid1()
    user = users[u"{0}".format(uid)] = User()

    sample.subscribe(user)
    return redirect("/{0}/".format(uid))

@app.route("/<uid>/")
def data_view(uid):
    # if no uid not available redirect back to home
    # and pick up a valid uid
    if not users.get(uid, False):
        return redirect(url_for("home"))
    return render_template(
        "index.html",
        data=sample.data,
        uid=uid,
    )

@app.route("/put/<uid>/", methods=["POST"])
def data_update(uid):
    if uid in users:
        sample.update(
            request.form['row'],
            request.form['field'],
            request.form['data']
        )
    return ''

@app.route("/add/<uid>/", methods=["POST"])
def data_add(uid):
    if uid in users:
        sample.add(request.form)
    return ''

@app.route("/poll/<uid>/", methods=["POST"])
def data_poll(uid):
    try:
        msg = users[uid].queue.get(timeout=10)
    except queue.Empty:
        msg = []
    return json.dumps(msg)

if __name__ == "__main__":
    http = WSGIServer(('', 5000), app)
    http.serve_forever()
