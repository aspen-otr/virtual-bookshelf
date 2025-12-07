import json
import flask
from flask import Flask, request, make_response, redirect

import db_layer

app = Flask(__name__)

# Magic numbers I guess (HTTP response codes mostly?/)
KEEP_HTTP_METHOD = 307

def logged_in():
    return request.cookies.get("user")

@app.route("/")
def default_route():
    resp = make_response(flask.render_template("index.html"))
    if request.args.get("logout") is not None:
        resp.set_cookie("user", expires = 0)
    return resp

@app.route("/login", methods = ["GET", "POST"])
def login_page():
    # POST: Log user into their /profile/<username>
    user = request.args.get("username")
    pw = request.args.get("password")

    if request.method == "POST":
        user = request.form["username"]
        pw = request.form["password"]

    if user is not None and pw is not None and db_layer.auth_user(user, pw):
        print(f"Logging in user: {user}")
        resp = make_response(redirect(f"/profile/{user}"))
        resp.set_cookie("user", user)
        return resp

    return flask.render_template("login.html")

@app.route("/register", methods = ["GET", "POST"])
def register_page():
    if request.method == "POST":
        uname = request.form["username"]
        dname = request.form["displayName"]
        p1 = request.form["password1"]
        p2 = request.form["password2"]
        if p1 != p2:
            return flask.render_template("register.html")
        if db_layer.register_user(uname, dname, p1) is None:
            return flask.render_template("register.html")
        return flask.redirect(f"/login?username={uname}&password={p1}")
    else:
        assert request.method == "GET"
        return flask.render_template("register.html")

@app.route("/profile/<username>")
def profile_page(username):
    return flask.render_template("profile.html")

if __name__ == "__main__":
    app.run(debug = True)
