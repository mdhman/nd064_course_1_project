import sqlite3
import datetime
import logging

from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    app.db_connection_count = app.db_connection_count + 1
    return connection

def close_db_connection(connection):
    connection.close()
    app.db_connection_count = app.db_connection_count - 1

def get_post_count():
    connection = get_db_connection()
    post_count = connection.execute('SELECT count(*) as count FROM posts').fetchone()
    close_db_connection(connection)
    return post_count['count']    

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    close_db_connection(connection)
    return post

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
app.db_connection_count = 0

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    close_db_connection(connection)
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.info('non-existing  404 page')
      return render_template('404.html'), 404
    else:
      app.logger.info('Article ' + post['title']+ ' retrieved!')
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('about page is retrieved')
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
            close_db_connection(connection)

            return redirect(url_for('index'))

    return render_template('create.html')


@app.route('/healthz')
def healthcheck():
    response = app.response_class(
            response=json.dumps({"result":"OK - healthy"}),
            status=200,
            mimetype='application/json'
    )
    app.logger.info('Status request successfull')
    app.logger.debug('DEBUG message')
    return response

@app.route('/metrics')
def metrics():
    app.logger.debug(app.db_connection_count)
    s = get_post_count()
    app.logger.debug(s)

    response = app.response_class(
            response=json.dumps({"status":"success","code":0,"data":{"db_connection_count": app.db_connection_count, "post_count": get_post_count()}}),
            status=200,
            mimetype='application/json'
    )
    app.logger.info('Metrics request successfull')
    return response

# start the application on port 3111
if __name__ == "__main__":
   logging.basicConfig(filename='app.log',format='%(asctime)s %(message)s',level=logging.DEBUG)
   app.run(host='0.0.0.0', port='3111')
