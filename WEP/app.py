# app.py
<<<<<<< HEAD
from flask import Flask, render_template, request, jsonify, redirect, url_for
from controller import app, admin_required
from model import init_db
from flask_login import login_required, current_user
=======
from flask import Flask
from controller import app
from model import init_db
>>>>>>> cccaacd336cadf923ad193e292b3b25cc18ad818

if __name__ == '__main__':
    init_db()  # Ensure the database is initialized before starting the app
    app.run(debug=True)