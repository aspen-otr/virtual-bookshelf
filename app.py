import json
import flask
from flask import Flask, request, make_response, redirect, jsonify

import db_layer

app = Flask(__name__, static_folder = "/")

# Magic numbers I guess (HTTP response codes mostly?/)
KEEP_HTTP_METHOD = 307

def logged_in():
    return request.cookies.get("user")

# Requests that ARE NOT pages
@app.route("/addToShelf/<int:shelf_id>/<isbn>", methods = ["POST"])
def add_to_shelf(shelf_id, isbn):
    db_layer.add_book_to_shelf(isbn, shelf_id)
    return jsonify(success = True)

@app.route("/removeFromShelf/<int:shelf_id>/<isbn>", methods = ["POST"])
def remove_from_shelf(shelf_id, isbn):
    db_layer.remove_book_from_shelf(isbn, shelf_id)
    return jsonify(success = True)

@app.route("/deleteShelf/<int:shelf_id>", methods = ["POST"])
def delete_shelf(shelf_id):
    db_layer.delete_shelf(shelf_id)
    return jsonify(success = True)

# Requests that ARE pages
@app.route("/")
def default_route():
    resp = make_response(flask.render_template("index.html"))
    if request.args.get("logout") is not None:
        resp.set_cookie("user", expires = 0)
    elif request.args.get("deleteaccount") is not None:
        if user := logged_in():
            db_layer.delete_user(user)
            resp.set_cookie("user", expires = 0)
    return resp

@app.route("/login", methods = ["GET", "POST"])
def login_page():
    if u := logged_in(): # Auto log in
        return flask.redirect(f"/profile/{u}")

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
        return flask.render_template("register.html")

@app.route("/search")
def search_page():
    terms = request.args.get("search")
    u = logged_in()
    if terms is None:
        if u:
            return flask.redirect(f"/profile/{u}")
        return flask.redirect("/login")
    results = db_layer.search_books(terms)
    print(results[0])
    if len(results) == 1:
        return flask.redirect(f"/book/{results[0]['isbn']}")
    return flask.render_template("search.html",
                                 search_results = results,
                                 user_shelves = db_layer.shelves_owned_by(u))

@app.route("/addShelf", methods = ["GET", "POST"])
def create_shelf_page():
    if request.method == "POST":
        if u := logged_in():
            name = request.form["shelfName"]
            desc = request.form["shelfDescription"]
            db_layer.create_shelf(name, desc, u)
            return flask.redirect("/profile")
    return flask.render_template("addShelf.html")

@app.route("/profile")
def default_profile():
    if u := logged_in():
        return flask.redirect(f"/profile/{u}")
    return flask.redirect("/login")

@app.route("/book/<isbn>")
def book_page(isbn):
    genres = db_layer.book_info(isbn)["genre"].split(",")
    first_two_genres = ", ".join(genres[:2])
    u = logged_in()
    reviews = db_layer.reviews_for(isbn)
    can_review = True
    if not u or [review for review in reviews if review["username"] == u]:
        can_review = False
    return flask.render_template("book.html",
                                 book = db_layer.book_info(isbn),
                                 reviews = reviews,
                                 can_review = can_review,
                                 genres = first_two_genres)

@app.route("/shelf/<int:shelf_id>")
def shelf_page(shelf_id):
    shelf = db_layer.shelf_info(shelf_id)
    owner = db_layer.user_info(shelf["username"])
    return flask.render_template("shelf.html",
                                 owner = owner,
                                 shelf = shelf,
                                 books = db_layer.books_on_shelf(shelf_id),
                                 current_user = logged_in())

@app.route("/profile/<username>")
def profile_page(username):
    return flask.render_template("profile.html",
                                 user = db_layer.user_info(username),
                                 currently_logged_in = logged_in() == username,
                                 reviews = db_layer.reviews_by_with_books(username),
                                 shelves = db_layer.shelves_owned_by_with_books(username))

@app.route("/addReview", methods = ["GET", "POST"])
def add_review_page():
    user = logged_in()
    isbn = request.args.get("isbn")
    print("addReview:", request.method, user, isbn)
    if not isbn:
        return flask.redirect("/profile")
    if not user:
        return flask.redirect(f"/book/{isbn}")
    if request.method == "POST":
        tagline = request.form["tagline"]
        content = request.form["content"]
        rating = request.form["rating"]
        db_layer.add_review(isbn, user, tagline, content, rating)
        return flask.redirect(f"/book/{isbn}")

    book = db_layer.book_info(isbn)
    return flask.render_template("addReview.html",
                                 user = user,
                                 book = book)

@app.route("/editUser", methods = ["GET", "POST"])
def edit_user_page():
    user = logged_in()
    if not user:
        return flask.redirect("/login")

    info = db_layer.user_info(user)
    if request.method == "GET":
        return flask.render_template("editUser.html", user = info)

    print(info)
    uname = request.form["username"] or user
    dname = request.form["displayName"] or info["display_name"]
    p1 = request.form["password1"]
    p2 = request.form["password2"]
    check = request.form["check_pw"]

    if not db_layer.auth_user(user, check):
        return
    if p1 != p2:
        return

    if db_layer.user_info(uname):
        return

    db_layer.update_user_info(user, uname, dname, p1 or None)
    resp = make_response(flask.redirect("/profile"))
    if user != uname:
        resp.set_cookie("user", uname)

    return resp

if __name__ == "__main__":
    app.run(debug = True)
