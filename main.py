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
    g.fullname = None
    g.email = None
    g.bankcard = None
    g.user_role = None

    if ('user_id' in session)\
            and ('nickname' in session)\
            and ('fullname' in session)\
            and ('email' in session)\
            and ('bankcard' in session)\
            and ('role' in session):
        g.user_id = session['user_id']
        g.nickname = session['nickname']
        g.fullname = session['fullname']
        g.email = session['email']
        g.bankcard = session['bankcard']
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

@server.route('/insurance',methods=['GET'])
def cases():
    return render_template('insurance/insurance_cases.html')

@server.route('/insurance/<price>', methods=['GET', 'POST'])
def insurance_form(price):
    if g.user_id == None:
        return redirect(url_for('login'))
    else:
        if request.method == 'GET':
            return render_template('insurance/insurance_form.html',
                                   price=price,
                                   fullname=g.fullname,
                                   email=g.email,
                                   bankcard=g.bankcard)
        else:

            connection = psycopg2.connect(
                server.config['SQLALCHEMY_DATABASE_URI']
            )
            connection.autocommit = True

            session['price'] = request.form['tariff']

            if session['price'] == 'light':
                real_price = 100000
            elif session['price'] == 'optimum':
                real_price = 150000
            elif session['price'] == 'premium':
                real_price = 200000
            else:
                raise Exception

            session['real_price'] = real_price

            start_date = request.form['start_date']
            end_date = request.form['end_date']

            cursor = connection.cursor()
            cursor.callproc('create_contract', (g.user_id, session["price"], str(real_price), end_date))

            status = cursor.fetchone()[0]
            session['contract_id'] = status
            connection.close()

            return render_template('payment.html')


@server.route('/users/me',methods=['GET'])
def my_cabinet():
    connection = psycopg2.connect(
        server.config['SQLALCHEMY_DATABASE_URI']
    )
    connection.autocommit = True

    cursor = connection.cursor()
    cursor.execute(f"SELECT get_customer_info({g.user_id})")
    result = cursor.fetchall()[0]


    (customer_id, full_name, age, email, login, passw, bank, role) = result[0][1:-1].split(',')

    cursor = connection.cursor()
    cursor.execute(f"select * from contracts where contracts.fk_customer_id = {customer_id}")
    contracts = cursor.fetchall()

    connection.close()

    g.insurance = []

    if contracts != []:
        for real_tup in contracts:
            g.insurance.append(' Страхування ' + str(real_tup[3]) + ' дійсне до ' + str(real_tup[5]))
    else:
        g.insurance = ['Договір не укладено']

    return render_template('users/profile_page.html',
                           full_name=full_name,
                           age=age,
                           email=email,
                           bankcard=bank,
                           insurance=g.insurance)

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
        session.pop('fullname', None)
        session.pop('email', None)
        session.pop('bankcard', None)
        session.pop('role', None)

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

            session['fullname'] = full_name
            session['email'] = email
            session['bankcard'] = bank
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
    session.pop('fullname', None)
    session.pop('email', None)
    session.pop('bankcard', None)
    session.pop('role', None)
    g.user_id = None
    g.nickname = None
    g.fullname = None
    g.email = None
    g.bankcard = None
    g.user_role = None

    return render_template('homepage.html')

if __name__ == '__main__':
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))