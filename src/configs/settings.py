from decouple import config


class Settings:
    SQLALCHEMY_DATABASE_URI = config("SQLALCHEMY_DATABASE_URI")

    AUTH_TOKEN = config("AUTH_TOKEN") 
    BASIC_AUTH_USERNAME = config("BASIC_AUTH_USERNAME")
    BASIC_AUTH_PASSWORD = config("BASIC_AUTH_PASSWORD")
