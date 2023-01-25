import os
from config import *
from flask import Flask, redirect, url_for, render_template, request, flash
import psycopg2
import hashlib
import datetime
from db_connection import registration

def to_sha(hash_string):
    sha_signature = hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature

server = Flask(__name__)

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

@server.route('/users/login', methods=['GET', 'POST'])
def login():
    return render_template('users/sign_in.html')

@server.route('/users/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('users/registration.html')
    if request.method == 'POST':
        connection = psycopg2.connect(SQLALCHEMY_DATABASE_URI)
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
            return render_template('users/registration.html')
    else:
        redirect(url_for('homepage'))

if __name__ == '__main__':
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))