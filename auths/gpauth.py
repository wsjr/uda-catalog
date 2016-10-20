from flask import request, flash, make_response
from flask import session as login_session
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.client import AccessTokenCredentials
import httplib2
import json
import requests


from models import model


GP_CLIENT_SECRET_JSON = './auths/gp_client_secret.json'

CLIENT_ID = json.loads(
    open(GP_CLIENT_SECRET_JSON, 'r').read())['web']['client_id']


class Authentication(object):

    """
    Google Plus Authentication
    """
    @classmethod
    def connect(self):
        # Validate state token
        if request.args.get('state') != login_session['state']:
            response = make_response(
                json.dumps('Invalid state parameter.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        # Obtain authorization code
        code = request.data

        try:
            # Upgrade the authorization code into a credentials object
            oauth_flow = flow_from_clientsecrets(
                GP_CLIENT_SECRET_JSON, scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(code)
        except FlowExchangeError:
            response = make_response(
                json.dumps('Failed to upgrade the authorization code.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Check that the access token is valid.
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
               % access_token)
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])
        # If there was an error in the access token info, abort.
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Verify that the access token is used for the intended user.
        login_session["credentials"] = credentials.access_token
        gplus_id = credentials.id_token['sub']
        if result['user_id'] != gplus_id:
            response = make_response(
                json.dumps("Token's user ID doesn't match given user ID."),
                401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Verify that the access token is valid for this app.
        if result['issued_to'] != CLIENT_ID:
            response = make_response(
                json.dumps("Token's client ID does not match app's."), 401)
            print "Token's client ID does not match app's."
            response.headers['Content-Type'] = 'application/json'
            return response

        stored_credentials = login_session.get('credentials')
        stored_gplus_id = login_session.get('gplus_id')
        if stored_credentials is not None and gplus_id == stored_gplus_id:
            response = make_response(
                json.dumps('Current user is already connected.'), 200)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Store the access token in the session for later use.
        login_session['access_token'] = credentials.access_token
        login_session['gplus_id'] = gplus_id

        # Get user info
        userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt': 'json'}
        answer = requests.get(userinfo_url, params=params)

        data = answer.json()

        login_session['username'] = data['name']
        login_session['picture'] = data['picture']
        login_session['email'] = data['email']
        # ADD PROVIDER TO LOGIN SESSION
        login_session['provider'] = 'google'

        # see if user exists, if it doesn't make a new one
        user_id = model.Users.get_user_id(data["email"])
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
        flash("You are now logged in as %s" % login_session['username'])
        return output

    @classmethod
    def disconnect(self):
        # Only disconnect a connected user.
        credentials = AccessTokenCredentials(
            login_session['credentials'], 'user-agent-value')
        if credentials is None:
            response = make_response(
                json.dumps('Current user not connected.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        access_token = credentials.access_token

        url = 'https://accounts.google.com/o/oauth2/revoke?'
        url += 'token=%s' % access_token
        h = httplib2.Http()
        result = h.request(url, 'GET')[0]
        if result['status'] != '200':
            # For whatever reason, the given token was invalid.
            response = make_response(
                json.dumps('Failed to revoke token for given user.'), 400)
            response.headers['Content-Type'] = 'application/json'
            return response
