"""This module codifies standard practices for scripted interactions with the 
web server file submission system.
"""

from lxml import html
import requests

from crds import config, log, utils, exceptions
from crds.python23 import *

class CrdsDjangoConnection(object):

    """This class handles CRDS authentication, basic GET, basic POST, and CRDS-style get/post.
    It also manages the CSRF token generated by Django to block form forgeries and CRDS instrument
    management/locking.
    """

    def __init__(self, locked_instrument="none", username=None, password=None, base_url=None):
        self.locked_instrument = locked_instrument
        self.username = username
        self.password = password
        self.base_url = base_url
        self.session = requests.session()
        self.session.headers.update({'referer': self.base_url})

    def abs_url(self, relative_url):
        """Return the absolute server URL constructed from the given `relative_url`."""
        return self.base_url + relative_url

    def dump_response(self, name, response):
        """Print out verbose output related to web `response` from activity `name`."""
        utils.divider(name=name)
        log.verbose("headers:\n", response.headers)
        utils.divider()
        log.verbose("status_code:", response.status_code)
        utils.divider()
        log.verbose("text:\n", response.text, verbosity=60)
        utils.divider()
        try:
            log.verbose("json:\n", response.json()) 
        except:
            pass
        utils.divider()

    def get(self, relative_url):
        """HTTP(S) GET `relative_url` and return the requests response object."""
        url = self.abs_url(relative_url)
        utils.divider(name="GET")
        log.verbose("GET:", url)
        response = self.session.get(url)
        self.dump_response("GET response:", response)
        self.check_error(response)
        return response

    def post(self, relative_url, *post_dicts, **post_vars):
        """HTTP(S) POST `relative_url` and return the requests response object."""
        url = self.abs_url(relative_url)
        vars = utils.combine_dicts(*post_dicts, **post_vars)
        utils.divider(name="POST " + url)
        log.verbose("POST:", vars)
        response = self.session.post(url, vars)
        self.dump_response("POST response: ", response)
        self.check_error(response)
        return response

    def repost(self, relative_url, *post_dicts, **post_vars):
        """First GET form from ``relative_url`,  next POST form to same
        url using composition of variables from *post_dicts and **post_vars.

        Maintain Django CSRF session token.
        """
        response = self.get(relative_url)

        csrf_token = html.fromstring(response.text).xpath(
            '//input[@name="csrfmiddlewaretoken"]/@value'
            )[0]
        post_vars['csrfmiddlewaretoken'] = csrf_token

        response = self.post(relative_url, *post_dicts, **post_vars)
        return response
    
    def login(self, next="/"):
        """Login to the CRDS website and proceed to relative url `next`."""
        response = self.repost(
            "/login/", 
            username = self.username,
            password = self.password, 
            instrument = self.locked_instrument,
            next = next,
            )
        self.check_login(response)
        
    def check_error(self, response):
        """Call fatal_error() if response contains an error_message <div>."""
        self._check_error(response, '//div[@id="error_message"]', "CRDS server error:")

    def check_login(self, reseponse):
        """Call fatal_error() if response contains an error_login <div>."""
        self._check_error(reseponse, '//div[@id="error_login"]', "Error logging into CRDS server:")

    def _check_error(self, response, xpath_spec, error_prefix):
        """Extract the `xpath_spec` text from `response`,  if present call fatal_error() with
        `error_prefix` and the response `xpath_spec` text.
        """
        error_msg_parse = html.fromstring(response.text).xpath(xpath_spec)
        error_message = error_msg_parse and error_msg_parse[0].text.strip()
        if error_message:
            if error_message.startswith("ERROR: "):
                error_message = error_message[len("ERROR: "):]
            log.fatal_error(error_prefix, error_message)

    def logout(self):
        """Login to the CRDS website and proceed to relative url `next`."""
        self.get("/logout/")
