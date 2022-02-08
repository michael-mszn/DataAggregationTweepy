import collections
import sys
import re

import pandas as pd
import numpy as np
import tweepy as tp

import custom_exceptions as ce
import pandas_config as pc
import tweepy_config as tc
import tweepy_authentication as tp_auth

API = tp_auth.aa

#  user.attribute : Column Header Name
#  Filter for raw user data
USERDATA_ATTRIBUTES = {"screen_name": "Username",
                       "url": "Profile Link",
                       "description": "Biography",
                       "created_at": "Account Creation Date",
                       "followers_count": "Follower Count",
                       "statuses_count": "Tweet Count",
                       "profile_image_url": "Profile Picture Link",
                       "profile_banner_url": "Profile Banner Link"}

#  ensures app functionality
ILLEGAL_CHARACTERS = re.compile(r"[ [\]\\\.\^\$\*\+\{\}\|\(\)\?\'\;\_\~\`\´\=\&\%\³\§\"\²\°\:\>\<\,\/\#]")
ILLEGAL_CHARACTERS_WITHOUT_HASHTAG = re.compile(r"[\[\]\\\.\^\$\*\+\{\}\|\(\)\?\'\;\_\~\`\´\=\&\%\³\§\"\²\°\:\>\<\,\/]")  # important for hashtag filtering functionality

#  generic invalid input template
INVALID_INPUT_STR_TEMPLATE = "Invalid input. Please follow the instructions!"

def get_hashtag_tweets():
    try:
        search_query = str(input("Please enter a hashtag as a search query! "))
        contains_illegal_character = ILLEGAL_CHARACTERS.search(search_query[1:]) or\
                                     ILLEGAL_CHARACTERS_WITHOUT_HASHTAG.search(search_query[0])  # Only tolerated special character is '#' on index 0
        if contains_illegal_character:
            raise ce.IllegalCharacterInHashtagException("Special characters are not allowed in hashtags. Please retry an input with no special characters.")
        first_character_not_hashtag = not search_query[0] == "#"
        if first_character_not_hashtag:  # Automatically adds hashtag in front of the search query if user did not
            search_query = "#" + search_query

        global search_hashtag
        search_hashtag = search_query  # Sets search_query as globally accessible variable
        print(f"Fetching tweets for {search_query}...")
        print()
        tweets = tp.Cursor(API.search, q=f"{search_query} -filter:retweets", tweet_mode="extended")\
            .items(tc.MIN_HASHTAG_TWEETS if tc.MAX_HASHTAG_TWEETS < tc.MIN_HASHTAG_TWEETS else tc.MAX_HASHTAG_TWEETS)  # Api call fetches atleast MIN_HASHTAG_TWEETS tweets,
        tweets = to_sequence(tweets)                                                                                   # normally MAX_HASHTAG_TWEETS tweets
        main_dataframe = pd.DataFrame()  # Main dataframe generation for the given search query
        main_dataframe["Users"] = pd.Series(np.array([tweet.user.screen_name for tweet in tweets]))
        main_dataframe["Tweets"] = pd.Series(np.array([tweet.full_text for tweet in tweets]))
        main_dataframe["Dates & Times"] = pd.Series(np.array([tweet.created_at for tweet in tweets]))
        main_dataframe["Likes"] = pd.Series(np.array([tweet.favorite_count for tweet in tweets]))
        main_dataframe["Retweets"] = pd.Series(np.array([tweet.retweet_count for tweet in tweets]))
        if main_dataframe.empty:
            raise ce.NoResultsFoundException(f"No results found for '{search_query}'.")

        else:
            main_dataframe = format_df(main_dataframe)
            print(main_dataframe)
            print()
            return main_dataframe

    except ce.NoResultsFoundException as e: # No results is not considered an error but the app can not continue further without data, app therefore quits
        print(e.strerror)
        sys.exit(0)

    except ce.IllegalCharacterInHashtagException as e: # Prevents special characters from crashing the app
        print(e.strerror)
        get_hashtag_tweets()


#  Turns Iterable into a Sequence to allow reusability
#  Status object from twitter is only iterable once and needs to be converted so it is iterable more than once
#  Premise for main_dataframe generation
def to_sequence(item_iterable):
    if not isinstance(item_iterable, collections.abc.Sequence):
        item_iterable = list(item_iterable)
    return item_iterable


#  Formats dataframe, function can be extended
def format_df(dataframe):
    dataframe.columns = dataframe.columns.str.lstrip()  # aligns columns properly
    #dataframe.columns = dataframe.columns.str.wrap(75)
    return dataframe


#  Prints most 10 occurring items for a selected category (currently supported: user tweet, hashtag)
#  When extending this functions supported categories, it is required to also extend 'get_category()'
def get_top_ten_category(category):
    global main_dataframe
    top_ten = [["", 0], ["", 0], ["", 0], ["", 0], ["", 0],
               ["", 0], ["", 0], ["", 0], ["", 0], ["", 0]]

    if category == "user_tweet":
        for username in main_dataframe["Users"]:
            if already_part_of_top_ten(top_ten, username):
                pass

            else:
                tweets_count = sum(main_dataframe["Users"] == username)  # counts how many tweets username published in the dataset
                top_ten = update_top_ten(top_ten, username, tweets_count)
        print_top_ten(top_ten, category)

    if category == "hashtag":
        for tweet in main_dataframe["Tweets"]:  # filter every raw tweet cell for hashtags, collect hashtags in a list
            word_list = split_tweet_into_words(tweet)
            hashtag_list = []
            for word in word_list:
                word_is_a_hashtag = word.startswith("#")
                if word_is_a_hashtag:
                    filter_unwanted_hashtags(word, hashtag_list)

            if hashtag_list:  # for every hashtag in a non empty list, iterate through tweet column and count occurrences
                for hashtag in hashtag_list:
                    if already_part_of_top_ten(top_ten, hashtag):
                        pass
                    elif hashtag == "#":
                        pass
                    else:
                        hashtags_count = sum(main_dataframe["Tweets"].str.contains(hashtag, case=False, regex=True))
                        top_ten = update_top_ten(top_ten, hashtag, hashtags_count)

        print_top_ten(top_ten, category)


#  Splits raw tweet into single words, returns list of words
def split_tweet_into_words(tweet):
    tweet = tweet.strip()
    tweet = re.sub(ILLEGAL_CHARACTERS_WITHOUT_HASHTAG, " ", tweet)
    return tweet.split()


#  Filters undesired hashtags
#  Undesired: Hashtag that is equal to the search query, hashtag that contains atleast 1 character from ILLEGAL_CHARACTERS
def filter_unwanted_hashtags(hashtag, hashtag_list):
    try:
        hashtag = hashtag.lower()
        contains_illegal_character = ILLEGAL_CHARACTERS.search(hashtag[1:])
        if contains_illegal_character:
            raise ce.IllegalCharacterInHashtagException(
                f"This hashtag contains a special character and will be ignored.")
        elif hashtag == search_hashtag.lower():
            pass
        else:
            hashtag_list.append(hashtag)
    except ce.IllegalCharacterInHashtagException:
        pass


#  If the item's name is already in the top 10, escapes for-loop and returns TRUE
def already_part_of_top_ten(top_ten, category):
    for item in top_ten:
        is_in_top_ten = True if category == item[0] else False
        if is_in_top_ten:
            break
    return is_in_top_ten


#  Checks if current item is eligible for top 10, replaces another item which score is lower
def update_top_ten(top_ten, category, score):
    top_ten_candidate = [category, score]
    for index, item in enumerate(top_ten):
        if score > item[1]:
            top_ten.insert(index, top_ten_candidate)
            del top_ten[-1]
            break  # App will malfunction if for-loop is not escaped (concurrent modification)!
    return top_ten


# Prints top ten of selected category
def print_top_ten(top_ten, category):
    rank = 1
    if category == "user_tweet":
        count_item = "tweet"
        print(f"Top 10 most active users for {search_hashtag} (out of latest {len(main_dataframe['Users'])} tweets):")
    if category == "hashtag":
        count_item = "occurrence"
        print(f"Top 10 most frequent hashtags in {search_hashtag} (out of latest {len(main_dataframe['Users'])} tweets):")
    for item in top_ten:
        is_plural = True if item[1] != 1 else False
        char = "s" if is_plural is True else ""
        print(f"{rank}. {item[0]} with {item[1]} {count_item}{char}")
        rank = rank + 1
    print()


#  Gets and prints MAX_FOLLOWERS followers of a given user
def get_followers():
    username = str(input("Please enter a username from the dataset to retrieve their followers. "))
    username_is_not_in_dataframe = validate_input(username)
    if username_is_not_in_dataframe:
        print("The given username is not part of the dataset. Please retry with a different username!")
        get_followers()

    else:
        followers_dataframe = generate_followers_df(username)
        user_has_zero_followers = followers_dataframe.empty
        if user_has_zero_followers:
            print(f"{username} has no followers.")

        else:
            followers_dataframe = format_df(followers_dataframe)
            print(followers_dataframe)
    print()


#  Checks if given user is part of main dataframe, if FALSE return TRUE
def validate_input(username):
    follower_dataframe = main_dataframe.loc[(main_dataframe["Users"] == username)]
    return follower_dataframe.empty


#  Returns dataframe of MAX_FOLLOWERS follower usernames
def generate_followers_df(username):
    followers = tp.Cursor(API.followers, username).items(tc.MAX_FOLLOWERS)
    followers_dataframe = pd.DataFrame()
    followers_dataframe["Followers"] = pd.Series(np.array([follower.screen_name for follower in followers]))
    return followers_dataframe


#  Gets MAX_USER_TWEETS tweets and essential profile data of MAX_FOLLOWERS users
def get_follower_userdata():
    username = str(input("Please enter a username from the dataset to retrieve their followers' userdata. "))
    username_is_not_in_dataframe = validate_input(username)
    if username_is_not_in_dataframe:
        print("The given username is not part of the dataset. Please retry with a different username!")
        get_follower_userdata()

    else:
        followers_dataframe = generate_followers_df(username)
        user_has_zero_followers = followers_dataframe.empty
        if user_has_zero_followers:
            print(f"{username} has no followers, no follower userdata can be retrieved.")

        else:
            for follower in followers_dataframe["Followers"]: # For each follower of the given user, get & print their tweets and profile data
                get_follower_tweets(followers_dataframe, username, follower) # Get and print Tweets
                profile_data = API.get_user(follower) # Get raw API profile data
                profile_attribute_value_list = []
                for attribute in USERDATA_ATTRIBUTES: # Filter profile data
                    profile_attribute_value = get_profile_attribute_value(attribute, profile_data)
                    profile_attribute_value_list.append(profile_attribute_value)
                follower_data_filtered = pd.concat(profile_attribute_value_list)
                print(follower_data_filtered)
                print(100*"-")


#  Gets and prints MAX_USER_TWEETS tweets for the current follower
def get_follower_tweets(followers_dataframe, username, follower):
    try:
        follower_counter = f'{followers_dataframe[followers_dataframe["Followers"] == follower].index.values[0] + 1}' \
                           f'/{len(followers_dataframe["Followers"])}' # Process progression counter
        follower_tweets_dataframe = pd.DataFrame()
        follower_tweets_dataframe["Tweets"] = pd.Series(np.array([follower_tweet.full_text for follower_tweet           # LOC fetches MAX_USER_TWEETS tweets from the current follower
                                                                  in tp.Cursor(API.user_timeline, screen_name=follower,
                                                                               tweet_mode="extended", include_rts=False)
                                                                 .items(tc.MAX_USER_TWEETS)]))
        follower_tweets_dataframe = format_df(follower_tweets_dataframe)
        user_has_no_tweets = follower_tweets_dataframe.empty
        if user_has_no_tweets:
            display_message = f"{follower} has no tweets."
            print_follower_tweets(display_message, follower, username, follower_counter)

        else:
            display_message = f"{follower_tweets_dataframe}"
            print_follower_tweets(display_message, follower, username, follower_counter)

    except tp.error.TweepError:  # Private twitter accounts can not be accessed
        display_message = "Twitter profile is set on private, unable to fetch tweets."
        print_follower_tweets(display_message, follower, username, follower_counter)


#  Print template for profile data
def print_follower_tweets(display_message, follower, username, follower_counter):
    print(f"""Tweets of twitter user {follower} following {username} ({follower_counter}):

{display_message}    

    """)


def get_profile_attribute_value(attribute, profile_data):
    try:
        profile_attribute_value = pd.Series(dtype=object)
        profile_attribute_value[USERDATA_ATTRIBUTES[attribute]] = getattr(profile_data, attribute)  # = profile_data.attribute
        profile_attribute_value.index = [USERDATA_ATTRIBUTES[attribute]]
    except AttributeError:  # Values can be sometimes missing and therefore not found (e.g. no profile banner), prevents app crash
        profile_attribute_value[USERDATA_ATTRIBUTES[attribute]] = "None"
    return profile_attribute_value


#  General user interface for the app
#  User is able to select a desired action or to terminate the app
def select_action():
    user_input = str(input(f"""Enter: 
- '1' to receive the top 10 of a selected category from the acquired dataset for {search_hashtag}
- '2' to receive the list of all followers of a selected user from the acquired dataset for {search_hashtag}
- '3' to receive all tweets and profile data of all followers of a selected user from the acquired dataset for {search_hashtag}
- 'q' to exit the app

"""))
    if user_input == '1':
        category = get_category()
        get_top_ten_category(category)
    elif user_input == '2':
        get_followers()
    elif user_input == '3':
        get_follower_userdata()
    elif user_input.lower() == 'q':
        print("Closing app...")
        sys.exit(0)
    else:
        print(INVALID_INPUT_STR_TEMPLATE)
    select_action()


#  allows user to select a top 10 category (currently supported: user tweet, hashtag)
def get_category():
    user_input = str(input(f"""Enter: 
- '1' to show the top 10 most active users or 
- '2' to show the top 10 most frequent hashtags for {search_hashtag} in the dataset

"""))
    if user_input == "1":
        category = "user_tweet"
        return category
    if user_input == "2":
        category = "hashtag"
        return category
    else:
        print(INVALID_INPUT_STR_TEMPLATE)
        get_category()


#  Main Program
pc.configurate_pd()
search_hashtag = ""
main_dataframe = get_hashtag_tweets()
select_action()
