import sqlite3
from loguru import logger
import sys
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                              (post_id,)).fetchone()
    connection.close()
    return post


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Define the main route of the web application
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)

    increase_db_connection_count(post_id)
    if post is None:
        logger.error('A non-existing article was accessed! "404"')
        return render_template('404.html'), 404
    else:
        logger.info('Article ' + '"' + post['title'] + '"' + ' loaded!')
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    logger.info('About Us page was loaded!')
    return render_template('about.html')

# Define the post creation functionality
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content, article_view) VALUES (?, ?, ?)',
                               (title, content, '0'))
            connection.commit()
            connection.close()

            logger.info('A new article ' + '"' + title + '"' + ' was created!')
            return redirect(url_for('index'))

    return render_template('create.html')


# Increment database connection by one per article visit
# 
# Args:
#   post_id: The id of the post that was just viewed.
# Returns:
#   The function returns the number of views for the article.
def increase_db_connection_count(post_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE posts SET article_view = article_view + 1 WHERE id = ?',
                (post_id,)).fetchone()
    conn.commit()
    conn.close()

# This code is used to get the total number of views of all the articles in the database.
#     It connects to the database and then fetches the total number of views of all the articles in the database.
#     It returns the total number of views of all the articles in the database.
#
# Args:
#   None
# Returns:
#   The total number of views for all articles in the database.
def get_db_connection_count():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    db_connection_count = cursor.execute(
        'SELECT SUM(article_view) FROM posts').fetchall()
    conn.close()
    db_connection_final_count = db_connection_count[0][0]
    return db_connection_final_count

# The get_count_pos() function connects to the database, creates a cursor, and then runs a SQL query to count the number of posts in the database. It then returns the count.
#
# Args:
#   None
# Returns:
#   The number of posts in the database.
def get_count_post():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    post_count = cursor.execute('SELECT COUNT(id) FROM posts').fetchone()
    conn.close()
    return post_count[0]

# Add the metrics endpoint that returns the number of posts and connection count of the DB
@app.route('/metrics')
def metrics():
    response = app.response_class(
        response=json.dumps(
            {"db_connection_count": get_db_connection_count(), "post_count": get_count_post()}),
        status=200,
        mimetype='application/json'
    )
    return response

# Add the healthcheck endpoint that returns 200 if the server is up and running
@app.route('/healthz')
def healthz():
    try:
        conn = get_db_connection()
        conn.execute('SELECT * FROM posts').fetchall()
        response = app.response_class(
            response=json.dumps({"result": "OK - healthy"}),
            status=200,
            mimetype='application/json'
        )
    except sqlite3.OperationalError as err:
        response = app.response_class(
            response=json.dumps({"result": "ERROR - unhealthy"}),
            status=500,
            mimetype='application/json'
        )
    return response


# Start the application on port 3111
if __name__ == "__main__":
    config = {
    "handlers": [
        {"sink": sys.stdout, "format": "<green>{time}</green> <level>{message}</level>"},
    ],
    "extra": {"user": "someone"}
    }
    logger.configure(**config)

    app.run(host='0.0.0.0', port='3111')
