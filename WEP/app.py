# app.py
from flask import Flask
from controller import app
from model import init_db

if __name__ == '__main__':
    init_db()  # Ensure the database is initialized before starting the app
    app.run(debug=True)