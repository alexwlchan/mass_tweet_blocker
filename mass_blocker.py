#!/usr/bin/env python
# -*- encoding: utf-8

import json
import os

import responder

from twitter import TwitterCredentials, TwitterSession


api = responder.API()

credentials = TwitterCredentials(
    consumer_api_key=os.environ["CONSUMER_API_KEY"],
    consumer_api_secret_key=os.environ["CONSUMER_API_SECRET_KEY"],
    access_token=os.environ["ACCESS_TOKEN"],
    access_token_secret=os.environ["ACCESS_TOKEN_SECRET"]
)

sess = TwitterSession(credentials)


@api.route("/")
def homepage(req, resp):
    resp.content = api.template("index.html")


def _prepare_mentions(mentions):
    all_tweets = {}

    for m in mentions:
        text = m["full_text"]

        for entity in m["entities"].get("media", []) + m["entities"].get("urls", []):
            text = text.replace(entity["url"], entity["display_url"])

        # TODO: Filter out tweets from yourself!

        tweet = {
            "text": text,
            "date": m["created_at"],
            "id_str": m["id_str"],
        }

        user = {
            "name": m["user"]["name"],
            "followers_count": m["user"]["followers_count"],
            "following_count": m["user"]["friends_count"],
            "created_at": m["user"]["created_at"],
            "profile_image": m["user"]["profile_image_url_https"],
        }

        user_handle = m["user"]["screen_name"]
        try:
            all_tweets[user_handle]["tweets"].append(tweet)
        except KeyError:
            all_tweets[user_handle] = {
                "user": user,
                "tweets": [tweet]
            }

    return all_tweets


@api.route("/get_mentions")
def get_mentions(req, resp):
    try:
        username = req.params["username"]
    except KeyError:
        resp.status_code = api.status_codes.HTTP_400
        resp.media = {"error": "You must pass a 'username' parameter"}
        return

    mentions = json.load(open("mentions.json"))

    by_user_mentions = _prepare_mentions(mentions)
    del by_user_mentions[username]
    resp.media = by_user_mentions

    # try:
    #     mentions = list(sess.search(f"to:{username}"))
    # except Exception as err:
    #     resp.status_code = api.status_codes.HTTP_500
    #     print(err)
    #     raise
    #
    # resp.media = list(_prepare_mentions(mentions))
    # json.dump(mentions, open("mentions.json", "w"))


if __name__ == "__main__":
    api.run()
