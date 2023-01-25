import os
from config import *
from flask import Flask, redirect, url_for, render_template

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

if __name__ == '__main__':
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))