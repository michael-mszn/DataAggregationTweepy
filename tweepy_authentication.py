import tweepy as tp

#  API Access credentials
ACCESS_TOKEN = "insert access token here"
ACCESS_TOKEN_SECRET = "insert secret access token here"

API_KEY = "insert api key here"
API_KEY_SECRET = "insert secret api key here"

authentication = tp.OAuthHandler(consumer_key=API_KEY, consumer_secret=API_KEY_SECRET)  # Verifying API Key
authentication.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)  # Creating API Access Token

api = tp.API(authentication, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)  # Accessing API
