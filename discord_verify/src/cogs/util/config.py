import configparser

# Load config keys
CONFIG = configparser.ConfigParser()
CONFIG.read("config.ini")
CONFIG.read("discord_secrets.ini")
