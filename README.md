# Schemas
Book
```
+--------------+---------------+------+-----+---------+-------+
| Field        | Type          | Null | Key | Default | Extra |
+--------------+---------------+------+-----+---------+-------+
| isbn         | varchar(10)   | NO   | PRI | NULL    |       |
| author       | varchar(250)  | YES  |     | NULL    |       |
| synopsis     | varchar(1000) | YES  |     | NULL    |       |
| genre        | varchar(1000) | YES  |     | NULL    |       |
| img          | varchar(500)  | YES  |     | NULL    |       |
| link         | varchar(300)  | YES  |     | NULL    |       |
| rating       | float         | YES  |     | NULL    |       |
| totalratings | int(11)       | YES  |     | NULL    |       |
| title        | varchar(300)  | YES  |     | NULL    |       |
+--------------+---------------+------+-----+---------+-------+
```
Own
```
+----------+-------------+------+-----+---------+-------+
| Field    | Type        | Null | Key | Default | Extra |
+----------+-------------+------+-----+---------+-------+
| id       | int(11)     | NO   | PRI | NULL    |       |
| username | varchar(20) | NO   | PRI | NULL    |       |
+----------+-------------+------+-----+---------+-------+
```
Shelf
```
+-------+--------------+------+-----+---------+----------------+
| Field | Type         | Null | Key | Default | Extra          |
+-------+--------------+------+-----+---------+----------------+
| id    | int(11)      | NO   | PRI | NULL    | auto_increment |
| name  | varchar(50)  | NO   |     | NULL    |                |
| desc  | varchar(300) | YES  |     | NULL    |                |
+-------+--------------+------+-----+---------+----------------+
```
OnShelf
```
+-------+-------------+------+-----+---------+-------+
| Field | Type        | Null | Key | Default | Extra |
+-------+-------------+------+-----+---------+-------+
| id    | int(11)     | NO   | PRI | NULL    |       |
| isbn  | varchar(10) | NO   | PRI | NULL    |       |
+-------+-------------+------+-----+---------+-------+
```
User
(pretend hashing the password matters, its not like you can just bypass with the cookie)
```
+-----------------+-------------+------+-----+---------+-------+
| Field           | Type        | Null | Key | Default | Extra |
+-----------------+-------------+------+-----+---------+-------+
| username        | varchar(20) | NO   | PRI | NULL    |       |
| display_name    | varchar(40) | NO   |     | NULL    |       |
| hashed_password | varchar(40) | NO   |     | NULL    |       |
+-----------------+-------------+------+-----+---------+-------+
```
Review
```
+----------+---------------+------+-----+---------+-------+
| Field    | Type          | Null | Key | Default | Extra |
+----------+---------------+------+-----+---------+-------+
| isbn     | varchar(10)   | NO   | PRI | NULL    |       |
| username | varchar(20)   | NO   | PRI | NULL    |       |
| tagline  | varchar(300)  | YES  |     | NULL    |       |
| content  | varchar(4096) | YES  |     | NULL    |       |
| rating   | float         | YES  |     | NULL    |       |
+----------+---------------+------+-----+---------+-------+
```
