import os
from config import Config
from flask import Flask, redirect, url_for, render_template, request, flash, g, session
import psycopg2
import hashlib
import datetime

def to_sha(hash_string):
    sha_signature = hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature

server = Flask(__name__)
server.config.from_object(Config)

@server.before_request
def before_request():
    g.user_id = None
    g.nickname = None
    g.user_role = None

    if ('user_id' in session) and ('nickname' in session) and ('role' in session):
        g.user_id = session['user_id']
        g.nickname = session['nickname']
        g.user_role = session['role']

@server.route('/')
def home():
    return redirect(url_for('homepage'))

@server.route('/home', methods=['GET', 'POST'])
def homepage():
    return render_template('homepage.html')

@server.route('/contacts', methods=['GET', 'POST'])
def contacts():
    return render_template('contacts.html')

@server.route('/cases',methods=['GET'])
def cases():
    return render_template('insurance/insurance_cases.html')

@server.route('/cases/<price>', methods=['GET', 'POST'])
def insurance_form(price):
    return render_template('insurance/insurance_form.html', price=price)

@server.route('/users/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('users/registration.html')
    if request.method == 'POST':
        connection = psycopg2.connect(
            server.config['SQLALCHEMY_DATABASE_URI']
        )
        connection.autocommit = True

        name = request.form['name']
        login = request.form['login']
        password1 = to_sha(request.form['pass1'])
        password2 = to_sha(request.form['pass2'])
        email = request.form['email']

        birth = request.form['date']
        print(birth)
        year = int(birth[:4])
        month = int(birth[5:7])
        day = int(birth[8:])

        now = datetime.datetime.now()
        n_year = now.year
        n_month = now.month
        n_day = now.day

        age = n_year - year
        if n_month < month or (n_month == month and n_day < day):
            age -= 1

        card = request.form['card']
        if password1 == password2:
            cursor = connection.cursor()
            cursor.callproc('register_customer', (login, password1, name, age, email, card))
            status = cursor.fetchone()[0]
            connection.close()
            if 'error' in status.lower():
                return render_template('users/registration.html')
            else:
                return render_template('homepage.html')
        else:
            connection.close()
            flash('passwords are not match')
            return render_template('users/registration.html')
    else:
        redirect(url_for('homepage'))

@server.route('/users/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('users/sign_in.html')
    if request.method == 'POST':
        session.pop('user_id', None)
        session.pop('nickname', None)

        connection = psycopg2.connect(
            server.config['SQLALCHEMY_DATABASE_URI']
        )
        connection.autocommit = True

        login_name = request.form['login']
        password = to_sha(request.form['pass'])

        cursor = connection.cursor()
        cursor.callproc('login_customer', (login_name, password))

        exit_code = cursor.fetchall()[0][0]
        if exit_code != -1:
            session['user_id'] = exit_code
            session['nickname'] = login_name

            cursor = connection.cursor()
            cursor.execute(f"SELECT get_customer_info({session['user_id']})")

            result = cursor.fetchall()[0]
            (customer_id, full_name, age, email, login, passw, bank, role) = result[0][1:-1].split(',')

            session['role'] = role

            connection.close()
            return redirect(url_for("homepage"))
        else:
            connection.close()
            flash('There is no user with that login')
            return render_template('users/sign_in.html')

@server.route('/users/logout')
def logout():
    session.pop('user_id', None)
    session.pop('nickname', None)
    g.user_id = None
    g.nickname = None

    return render_template('homepage.html')

if __name__ == '__main__':
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))