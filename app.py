# DataShare
#
# share data view between multiple users
#
# when person visits site assign them a uuid
# data updates happen in the following manners
# - add new row
# - update specific cell

import uuid

from flask import Flask, render_template, redirect, url_for
from gevent import queue
from gevent.pywsgi import WSGIServer

app = Flask(__name__)
app.debug = True

class DataSample(object):
    """Data wrapper"""
    def __init__(self):
        self.users = set()
        self.data = [
            ('Joe', 'Bloggs', 10, 20, 30),
            ('Bill', 'Lewis', 12, 17, 34),
            ('Jack', 'Higgins', 15, 42, 3),
        ]

    def add(self, data):
        for user in self.users:
            user.queue.put_nowait(data)
        self.data.append(data)

    def update(self, data):
        for user in self.users:
            user.queue.put_nowait(data)
        self.data.update(data)

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
    users[uid] = User()

    sample.subscribe(users[uid])
    return redirect("/{0}/".format(uid))

@app.route("/<uid>/")
def data_view(uid):
    return render_template(
        "index.html",
        data=sample.data,
    )

if __name__ == "__main__":
    http = WSGIServer(('', 5000), app)
    http.serve_forever()
