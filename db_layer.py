import mariadb
from contextlib import contextmanager
from hashlib import sha1

conf = {
    "user": "aspen",
    "password": "aspen",
    "host": "localhost",
    "port": 3306,
    "database": "cs366"
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
        conn.commit()
        conn.close()

def load_procs():
    procs = [
        """
        CREATE PROCEDURE IF NOT EXISTS DeleteShelf(IN gid INT)
        BEGIN
        DELETE FROM Shelf WHERE id = gid;
        DELETE FROM Own WHERE id = gid;
        DELETE FROM OnShelf WHERE id = gid;
        END
        """,
        # Auto-aborts before running more username-altering goings-on.
        """
        CREATE PROCEDECURE IF NOT EXISTS UpdateUser
        (IN cur VARCHAR(20) NOT NULL, IN uname VARCHAR(20),
            IN dname VARCHAR(40), IN hash VARCHAR(40))
        BEGIN
        IF dname IS NOT NULL THEN
        UPDATE User
        SET display_name = dname
        WHERE username = cur;
        END IF;

        IF hash IS NOT NULL THEN
        UPDATE User
        SET hashed_password = hash
        WHERE username = cur;
        END IF;

        IF uname IS NOT NULL THEN
        UPDATE User
        SET username = uname
        WHERE username = cur;

        UPDATE Own
        SET username = uname
        WHERE username = cur;

        UPDATE Review
        SET username = uname
        WHERE username = cur;

        END IF;
        END
        """,
        """
        CREATE PROCEDURE IF NOT EXISTS DeleteUser(IN uname VARCHAR(20) NOT NULL)
        BEGIN

        DELETE FROM User WHERE username = uname;

        DECLARE cur CURSOR FOR
        SELECT id
        FROM Shelf NATURAL JOIN Own
        WHERE username = uname;

        DECLARE @done BOOLEAN DEFAULT false;
        DECLARE @shelf INT DEFAULT 0;
        DECLARE CONTINUE HANDLER FOR NOT FOUND SET @done = true;

        OPEN cur;
        
        del_shelf: LOOP

        IF @done = true THEN
        LEAVE del_shelf;
        END IF;

        CALL DeleteShelf(@shelf);

        END LOOP;

        CLOSE cur;

        DELETE FROM Review
        WHERE username = uname;

        END
        """
    ]
    with db_cur() as cur:
        for proc in procs:
            cur.execute(proc)

# Fetching
def user_info(username):
    with db_cur() as cur:
        cur.execute("SELECT * FROM User WHERE username = ?", (username,))
        return cur.fetchone()

def book_info(isbn):
    with db_cur() as cur:
        cur.execute("SELECT * FROM Book WHERE isbn = ?", (isbn,))
        return cur.fetchone()

def shelf_info(shelf_id):
    with db_cur() as cur:
        cur.execute("SELECT * FROM Shelf WHERE id = ?", (shelf_id,))
        res = cur.fetchone()
        cur.execute("SELECT username FROM Own WHERE id = ?", (shelf_id,))
        res["username"] = cur.fetchone()["username"]
        return res

def books_on_shelf(shelf_id):
    with db_cur() as cur:
        cur.execute("SELECT Book.* FROM Book NATURAL JOIN OnShelf WHERE OnShelf.id = ?", (shelf_id,))
        return list(cur.fetchall())

def shelves_owned_by(username):
    with db_cur() as cur:
        cur.execute("SELECT Shelf.* FROM Shelf NATURAL JOIN Own WHERE username = ?", (username,))
        return cur.fetchall()

def shelves_owned_by_with_books(username):
    shelves = shelves_owned_by(username)
    books = []
    res = []
    for shelf in shelves:
        res.append({
            "shelf": shelf,
            "books": books_on_shelf(shelf["id"])
        })
    return res

def reviews_for(isbn):
    with db_cur() as cur:
        cur.execute("SELECT * FROM Review WHERE isbn = ?", (isbn,))
        return list(cur.fetchall())

def reviews_by(username):
    with db_cur() as cur:
        cur.execute("SELECT * FROM Review WHERE username = ?", (username,))
        return list(cur.fetchall())

def reviews_by_with_books(username):
    reviews = reviews_by(username)
    res = []
    for rev in reviews:
        res.append({
            "review": rev,
            "book": book_info(rev["isbn"])
        })
    return res

def search_books(terms):
    if terms is None or len(terms) == 0:
        return title_search("")
    if is_isbn(terms):
        return [book_info(terms)]
    split = terms.split(":", 1)
    if len(split) == 1 or len(split[1]) == 0:
        return title_search(split[0])
    cat, spec = split
    if cat == "title":
        return title_search(spec)
    elif cat == "genre":
        return genre_search(spec)
    elif cat == "author":
        return author_search(spec)
    elif cat == "rating":
        split = spec.split("-", 1)
        low = float(split[0])
        if len(split) > 1:
            high = float(split[1])
        else:
            high = 5.0
        low = max(low, 0.0)
        high = max(high, 5.0)
        return rating_search(low, high)
    return title_search(spec)

def title_search(title):
    with db_cur() as cur:
        cur.execute("SELECT * FROM Book WHERE title LIKE CONCAT('%', ?, '%')", (title,))
        return list(cur.fetchall())

def author_search(author):
    with db_cur() as cur:
        cur.execute("SELECT * FROM Book WHERE author LIKE CONCAT('%', ?, '%')", (author,))
        return list(cur.fetchall())

def genre_search(genre):
    with db_cur() as cur:
        cur.execute("SELECT * FROM Book WHERE genre LIKE CONCAT('%', ?, '%')", (genre,))
        return list(cur.fetchall())

def rating_search(low, high):
    with db_cur() as cur:
        cur.execute("SELECT * FROM Book WHERE (rating >= ? AND rating <= ?)", (low, high))
        return list(cur.fetchall())

def true_average_rating(isbn):
    with db_cur() as cur:
        cur.execute("SELECT COUNT(isbn), SUM(rating) FROM Review WHERE isbn = ?", (isbn,))
        review_count, review_total = cur.fetchone()
        cur.execute("SELECT rating, totalratings FROM Book WHERE isbn = ?", (isbn,))
        dbrc, dbrt = cur.fetchone()
        rat_total = dbrc * dbrt + review_total
        return rat_total / (dbrt + review_count)

# Updating/Inserting
def add_book_to_shelf(isbn, shelf_id):
    with db_cur() as cur:
        cur.execute("SELECT id, isbn FROM OnShelf WHERE isbn = ?", (isbn,))
        if not (isbn, shelf_id) in cur.fetchall():
            cur.execute("INSERT INTO OnShelf (id, isbn) VALUES (?, ?)", (shelf_id, isbn))

def remove_book_from_shelf(isbn, shelf_id):
    with db_cur() as cur:
        cur.execute("DELETE FROM OnShelf WHERE (isbn = ? AND id = ?)", (isbn, shelf_id))

def create_shelf(name, description, owner): # Returns shelf ID
    if user_info(owner) is None:
        return -1
    with db_cur() as cur:
        cur.execute("INSERT INTO Shelf (name, `desc`) VALUES (?, ?)", (name, description))
        shelf_id = cur.lastrowid
        cur.execute("INSERT INTO Own (id, username) VALUES (?, ?)", (shelf_id, owner))
        return shelf_id

def register_user(username, display_name, password):
    if user_info(username) is not None:
        return None
    with db_cur() as cur:
        pw = hash_password(password)
        cur.execute("INSERT INTO User (username, display_name, hashed_password) VALUES (?, ?, ?)", (username, display_name, pw))
    create_shelf("Liked Books", None, username)
    return username

def delete_shelf(shelf_id):
    with db_cur() as cur:
        cur.callproc('DeleteShelf', [shelf_id])

def delete_user(username):
    with db_cur() as cur:
        cur.callproc('DeleteUser', [username])

def add_review(isbn, username, tagline, content, rating):
    with db_cur() as cur:
        cur.execute("INSERT INTO Review (isbn, username, tagline, content, rating) VALUES (?, ?, ?, ?, ?)",
                    (isbn, username, tagline, content, rating))

def update_user_info(old_name, username, display_name, password):
    if password is not None:
        password = hash_password(password)

    with db_cur() as cur:
        cur.callproc('UpdateUser',
                     [old_name,
                      username or None,
                      display_name or None,
                      password or None])

# Extraneous utilities
def hash_password(plaintext):
    return sha1(bytes(plaintext, "utf8")).hexdigest()

def auth_user(username, plaintext_password):
    u = user_info(username)
    return u is not None and u["hashed_password"] == hash_password(plaintext_password)

def is_isbn(string):
    return len(string) == 10 and (string.isdigit() or (string[:9].isdigit() and string[9] == 'X'))
