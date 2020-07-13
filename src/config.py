import os

class Config(object):
    SECRET_KEY = os.getenv('SECRET_KEY')
    UPLOAD_FOLDER = './static/images/stages_calculation'
    
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_SSL = False
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'juangv750@gmail.com'
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')

class DevelopmentConfig(Config):
    SQLALCHEMY_TRACK_MODIFICATIONS = False