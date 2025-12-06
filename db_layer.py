import mariadb
from contextlib import contextmanager
from hashlib import sha1

conf = {
    "user": "aspen",
    "password": "aspen",
    "host": "localhost",
    "port": 3306,
    "database": "db"
}

@contextmanager
def db_cur(**kwargs): # Supply with db_cur(conf = { ... })
    db_conf = kwargs.get("conf", conf)
    conn = mariadb.connect(**db_conf)
    cur = conn.cursor(dictionary = True)
    try:
        yield cur
    finally:
        cur.close()

def db_exec(func, *args, **kwargs):
    res = None
    with db_cur() as cur:
        res = func(cur, *args)
    return res

# Fetching
def user_info(username):
    with db_cur() as cur:
        cur.execute("SELECT * FROM User WHERE username = ?", (username,))
        return cur.fetchone()

def book_info(isbn):
    with db_cur() as cur:
        cur.execute("SELECT * FROM Book WHERE isbn = ?", (isbn,))
        return cur.fetchone()

def books_on_shelf(shelf_id):
    with db_cur() as cur:
        cur.execute("SELECT Book.* FROM Book NATURAL JOIN OnShelf WHERE OnShelf.id = ?", (shelf_id,))

def shelves_owned_by(username):
    with db_cur() as cur:
        cur.execute("SELECT Shelf.* FROM Shelf NATURAL JOIN Own WHERE username = ?", (username,))

# Updating/Inserting
def add_book_to_shelf(isbn, shelf_id):
    with db_cur() as cur:
        cur.execute("INSERT INTO OnShelf (id, isbn) VALUES (?, ?)", (shelf_id, isbn))
        cur.commit()

def create_shelf(name, description): # Returns shelf ID
    with db_cur() as cur:
        cur.execute("INSERT INTO Shelf (shelf_name, shelf_desc) VALUES (?, ?)", (name, description))
        cur.commit()
        cur.execute("SELECT max(id) FROM Shelf")
        return cur.fetchone()

# Extraneous utilities
def hash_password(plaintext):
    return sha1(bytes(plaintext, "utf8")).hexdigest()

def auth_user(username, plaintext_password):
    u = user_info(username)
    return u is not None and u["hashed_password"] == hash_password(plaintext_password)
