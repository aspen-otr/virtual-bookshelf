import json
import flask
from flask import Flask, request, make_response, redirect

import db_layer

app = Flask(__name__)

def logged_in():
    return request.cookies.get("user")

@app.route("/")
def default_route():
    return flask.render_template("index.html")

@app.route("/login")
def login_page():
    return flask.render_template("login.html")

@app.route("/register")
def register_page():
    return flask.render_template("register.html")

@app.route("/profile", methods = ["GET", "POST"])
def profile_page():
    if request.method == "POST": # Log user in
        username = request.form["username"]
        password = request.form["password"]

        if db_layer.auth_user(username, password):
            print(f"Logging in {username}")
            response = make_response(redirect(f"/profile?username={username}"))
            response.set_cookie("user", username)
            return response
        return flask.redirect("/login")
    else:
        return flask.render_template("profile.html")

if __name__ == "__main__":
    app.run(debug = True)
