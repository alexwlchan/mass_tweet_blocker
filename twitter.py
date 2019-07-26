# -*- encoding: utf-8
"""
Code for interacting with the Twitter API.

Taken from https://github.com/alexwlchan/backup_twitter
"""

import copy
import logging

import attr
from requests_oauthlib import OAuth1Session


LOGGER = logging.getLogger(__name__)

API_URL = "https://api.twitter.com/1.1"


@attr.s
class TwitterCredentials:
    """
    Credentials for the Twitter API.

    Get credentials by creating an app at https://developer.twitter.com/en/apps,
    then passing in keys from the "Keys and tokens" tab.
    """
    consumer_api_key = attr.ib()
    consumer_api_secret_key = attr.ib()
    access_token = attr.ib()
    access_token_secret = attr.ib()


class TwitterSession:
    """
    Class that wraps interactions from the Twitter API
    """

    def __init__(self, credentials):
        self.oauth_session = self._create_oauth_session(credentials)

    @staticmethod
    def _create_oauth_session(credentials):
        sess = OAuth1Session(
            client_key=credentials.consumer_api_key,
            client_secret=credentials.consumer_api_secret_key,
            resource_owner_key=credentials.access_token,
            resource_owner_secret=credentials.access_token_secret
        )

        # Raise an exception on responses that don't return a 200 OK.
        # See https://alexwlchan.net/2017/10/requests-hooks/

        def raise_for_status(resp, *args, **kwargs):
            resp.raise_for_status()

        sess.hooks["response"].append(raise_for_status)

        return sess

    def _http_get(self, path, *args, **kwargs):
        kwargs["params"]["tweet_mode"] = "extended"
        return self.oauth_session.get(API_URL + path, *args, **kwargs)

    def search(self, query):
        # https://developer.twitter.com/en/docs/tweets/search/api-reference/get-search-tweets.html
        initial_params = {
            "q": query,
            "count": 100,
        }

        yield from self._paginated_responses_by_max_id(
            "/search/tweets.json",
            initial_params=initial_params,
            get_tweets_from_resp=lambda resp: resp["statuses"]
        )

    def _paginated_responses_by_max_id(
        self,
        path,
        initial_params,
        get_tweets_from_resp=lambda resp: resp
    ):
        params = copy.deepcopy(initial_params)
        while True:
            LOGGER.info("Making request to %s with %r", path, params)

            resp = self._http_get(path, params=params)

            yield from get_tweets_from_resp(resp.json())

            try:
                params["max_id"] = min(
                    tweet["id"] for tweet in get_tweets_from_resp(resp.json())) - 1
            except ValueError:
                # Empty response: nothing more to do
                break
