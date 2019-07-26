#!/usr/bin/env python
# -*- encoding: utf-8

import json

import responder

from twitter import TwitterCredentials, TwitterSession


api = responder.API()

credentials = TwitterCredentials(
    **json.load(open("/Users/alexwlchan/repos/junkdrawer/backups/twitter/auth2.json")))

sess = TwitterSession(credentials)


@api.route("/")
def homepage(req, resp):
    resp.content = api.template("index.html")


def _prepare_mentions(mentions):
    for m in mentions:
        text = m["full_text"]

        for entity in m["entities"].get("media", []) + m["entities"].get("urls", []):
            text = text.replace(entity["url"], entity["display_url"])

        # TODO: Filter out tweets from yourself!

        yield {
            "text": text,
            "user_handle": m["user"]["screen_name"],
            "user_name": m["user"]["name"],
            "user_followers_count": m["user"]["followers_count"],
            "user_following_count": m["user"]["friends_count"],
            "user_created_at": m["user"]["created_at"],
            "user_profile_image": m["user"]["profile_image_url_https"],
            "date": m["created_at"],
            "id_str": m["id_str"],
        }


@api.route("/get_mentions")
def get_mentions(req, resp):
    try:
        username = req.params["username"]
    except KeyError:
        resp.status_code = api.status_codes.HTTP_400
        resp.media = {"error": "You must pass a 'username' parameter"}
        return

    mentions = json.load(open("mentions.json"))
    resp.media = list(_prepare_mentions(mentions))

    # try:
    #     mentions = list(sess.search(f"to:{username}"))
    # except Exception as err:
    #     resp.status_code = api.status_codes.HTTP_500
    #     print(err)
    #     raise
    #
    # resp.media = list(mentions)
    # json.dump(mentions, open("mentions.json", "w"))


if __name__ == "__main__":
    api.run()
