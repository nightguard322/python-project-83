from flask import (
    Flask,
    render_template, 
    request, 
    flash,
    get_flashed_messages,
    redirect,
    url_for
)
from dotenv import load_dotenv
import os
import psycopg2
from psycopg2.extras import DictCursor
from functools import wraps
import validators
from urllib.parse import urlparse

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY']=os.getenv('SECRET_KEY')
DATABASE_URL = os.getenv('DATABASE_URL')

@app.before_request
def check_db_connection():
    if not conn or conn.closed:  # Render может закрывать неактивные соединения
        conn = psycopg2.connect(
            DATABASE_URL,
            sslmode="require")

def handle_errors(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except psycopg2.Error as e:
            return f'Database error, - {e}', 500
        except Exception as e:
            return f'Common error - {e}', 500
    return wrapper


@app.route('/')
@handle_errors
def index():
    messages = get_flashed_messages(with_categories=True)
    return render_template(
        'index.html',
        messages=messages
    )


@app.route('/urls')
@handle_errors
def urls_index():
    with conn.cursor(cursor_factory=DictCursor) as c:
        c.execute('SELECT * FROM urls ORDER BY id DESC')
        urls = c.fetchall()
        conn.commit()
    return render_template(
        '/urls/index.html',
        urls=urls
    )


@app.post('/urls')
@handle_errors
def urls_store():
    url_name = request.form.get('url')
    if not validators.url(url_name):
        flash('Некорректный URL', 'error')
        return render_template(
            'index.html',
            url_name=url_name
    )
    with conn.cursor(cursor_factory=DictCursor) as c:
        c.execute('SELECT * FROM urls WHERE name = %s', (url_name, ))
        existing_url = c.fetchone()
        if existing_url:
            id = existing_url['id']
            flash('Страница уже существует', 'warning')
        else:
            parsed = urlparse(url_name)
            c.execute('INSERT INTO urls (name) VALUES (%s) RETURNING id;',
                (f"{parsed.scheme}://{parsed.hostname}", ))
            id = c.fetchone()[0]
            flash('Страница успешно добавлена', 'success')
        conn.commit()
    return redirect(url_for('urls_show', id=id))


@app.route('/urls/<int:id>')
@handle_errors
def urls_show(id):
    with conn.cursor(cursor_factory=DictCursor) as c:
        c.execute('SELECT * FROM urls WHERE id = %s', (id, ))
        url = c.fetchone()
    if not url:
        return 'Url not found', 404
    conn.commit()
    return render_template(
        '/urls/show.html',
        url=url
    )
