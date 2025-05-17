# app.py
from flask import Flask, render_template, request, jsonify, redirect, url_for
from controller import app, admin_required
from model import init_db
from flask_login import login_required, current_user

if __name__ == '__main__':
    init_db()  # Ensure the database is initialized before starting the app
    app.run(debug=True)