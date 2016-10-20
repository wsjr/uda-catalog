from flask import request, flash, make_response
from flask import session as login_session
import httplib2
import json
import requests


from models import model


FB_CLIENT_SECRET_JSON = './auths/fb_client_secret.json'


class Authentication(object):

    """
    Facebook Authentication
    """
    @classmethod
    def connect(self):
        if request.args.get('state') != login_session['state']:
            response = make_response(
                json.dumps('Invalid state parameter.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        access_token = request.data
        print "access token received %s " % access_token

        app_id = json.loads(open(FB_CLIENT_SECRET_JSON, 'r').read())[
            'web']['app_id']
        app_secret = json.loads(
            open(FB_CLIENT_SECRET_JSON, 'r').read())['web']['app_secret']
        raw_url = 'https://graph.facebook.com/oauth/access_token?'
        raw_url += 'grant_type=fb_exchange_token&client_id=%s&'
        raw_url += 'client_secret=%s&fb_exchange_token=%s'
        url = raw_url % (app_id, app_secret, access_token)
        h = httplib2.Http()
        result = h.request(url, 'GET')[1]

        # Use token to get user info from API
        userinfo_url = "https://graph.facebook.com/v2.4/me"
        # strip expire tag from access token
        token = result.split("&")[0]

        raw_url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email'
        url = raw_url % token
        h = httplib2.Http()
        result = h.request(url, 'GET')[1]
        # print "url sent for API access:%s"% url
        # print "API JSON result: %s" % result
        data = json.loads(result)
        login_session['provider'] = 'facebook'
        login_session['username'] = data["name"]
        login_session['email'] = data["email"]
        login_session['facebook_id'] = data["id"]

        # The token must be stored in the login_session in order to properly
        # logout, let's strip out the information before the equals sign in our
        # token
        stored_token = token.split("=")[1]
        login_session['access_token'] = stored_token

        # Get user picture
        raw_url = 'https://graph.facebook.com/v2.4/me/picture?'
        raw_url += '%s&redirect=0&height=200&width=200'
        url = raw_url % token
        h = httplib2.Http()
        result = h.request(url, 'GET')[1]
        data = json.loads(result)

        login_session['picture'] = data["data"]["url"]

        # see if user exists
        user_id = model.Users.get_user_id(login_session['email'])
        if not user_id:
            user_id = model.Users.create_entry(
                username=login_session['username'],
                email=login_session['email'],
                picture=login_session['picture'])
        login_session['user_id'] = user_id

        output = ''
        output += '<h1>Welcome, '
        output += login_session['username']

        output += '!</h1>'
        output += '<img src="'
        output += login_session['picture']
        output += ' " style = "width: 300px; height: 300px;'
        output += 'border-radius: 150px;-webkit-border-radius: 150px;'
        output += '-moz-border-radius: 150px;"> '

        flash("Now logged in as %s" % login_session['username'])
        return output

    @classmethod
    def disconnect(self):
        facebook_id = login_session['facebook_id']
        # The access token must me included to successfully logout
        access_token = login_session['access_token']
        url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (
            facebook_id, access_token)
        h = httplib2.Http()
        result = h.request(url, 'DELETE')[1]
        output = "You have been logged out"
        return output
