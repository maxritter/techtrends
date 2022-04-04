import sqlite3
import os
import logging
import sys
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# To get number of connections
connection_count = 0

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global connection_count

    connection_count += 1
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

    if post is None:
        app.logger.error('A non-existing article was accessed! "404"')
        return render_template('404.html'), 404
    else:
        app.logger.info('Article ' + '"' + post['title'] + '"' + ' loaded!')
        return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('About Us page was loaded!')
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
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                               (title, content))
            connection.commit()
            connection.close()

            app.logger.info('A new article ' + '"' + title + '"' + ' was created!')
            return redirect(url_for('index'))

    return render_template('create.html')


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
            {"db_connection_count": connection_count, "post_count": get_count_post()}),
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
    loglevel = os.getenv("LOGLEVEL", "DEBUG").upper()
    loglevel = (
        getattr(logging, loglevel)
        if loglevel in ["CRITICAL", "DEBUG", "ERROR", "INFO", "WARNING", ]
        else logging.DEBUG
    )

    # Set logger to handle STDOUT and STDERR
    stdout_handler = logging.StreamHandler(sys.stdout)
    stderr_handler = logging.StreamHandler(sys.stderr)
    handlers = [stderr_handler, stdout_handler]

    # Create the log file and format each log
    logging.basicConfig(
        format='%(levelname)s:%(name)s:%(asctime)s, %(message)s',
        level=loglevel,
        datefmt='%m-%d-%Y, %H:%M:%S',
        handlers=handlers
    )

    app.run(host='0.0.0.0', port='3111')
