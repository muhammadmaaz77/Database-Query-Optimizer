import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    DATABASE_DIR = os.path.join(BASE_DIR, 'data')
    DATABASE_PATH = os.path.join(DATABASE_DIR, 'university.db')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'query-optimizer-simulator-secret-key')
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
