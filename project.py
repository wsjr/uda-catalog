from flask import Flask, render_template, request, redirect, jsonify, \
                  url_for, flash, make_response
from flask import session as login_session
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from datetime import datetime
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
from oauth2client.client import AccessTokenCredentials
import random
import string
import httplib2
import json
import requests

app = Flask(__name__)


GP_CLIENT_SECRET_JSON = 'gp_client_secret.json'
FB_CLIENT_SECRET_JSON = 'fb_client_secret.json'

CLIENT_ID = json.loads(
    open(GP_CLIENT_SECRET_JSON, 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"


engine = create_engine('sqlite:///catalogwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

LATEST_ITEMS_TO_DISPLAY_COUNT = 8


def getCategoryByName(name):
    try:
        return session.query(Category).filter_by(name=name).one()
    except:
        return None


def getCategoryById(cid):
    try:
        return session.query(Category).filter_by(id=cid).one()
    except:
        return None


def getCategories():
    try:
        return session.query(Category).all()
    except:
        return None


def getItem(title, cid):
    try:
        return session.query(Item).filter_by(title=title)\
                                  .filter_by(category_id=cid)\
                                  .one()
    except:
        return None


def getItemById(iid):
    try:
        return session.query(Item).filter_by(id=iid).one()
    except:
        return None


def getItemsByCategoryId(cid):
    try:
        return session.query(Item).order_by(desc(Item.timestamp))\
                                  .filter_by(category_id=cid)
    except:
        return None


def deleteItemsByCategoryId(cid):
    try:
        session.query(Item).filter_by(category_id=cid).delete()
        session.commit()
    except:
        return None        

def getLatestItems():
    try:
        return session.query(Item).order_by(desc(Item.timestamp))\
                                  .limit(LATEST_ITEMS_TO_DISPLAY_COUNT)
    except:
        return None


#############
# LOGIN
############


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open(FB_CLIENT_SECRET_JSON, 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open(FB_CLIENT_SECRET_JSON, 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.4/me"
    # strip expire tag from access token
    token = result.split("&")[0]


    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout, let's strip out the information before the equals sign in our token
    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    # Get user picture
    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']

    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

    flash("Now logged in as %s" % login_session['username'])
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(GP_CLIENT_SECRET_JSON, scope='')
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
            json.dumps("Token's user ID doesn't match given user ID."), 401)
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
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
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
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    credentials = AccessTokenCredentials(login_session['credentials'], 'user-agent-value')
    #credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

###############
# User related
###############

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def redirectHome():
    return redirect(url_for('listCatalogsAndLatestItems'))


# JSON ENDPOINT
@app.route('/catalog.json')
def getJSON():
    # Get all categories
    categories = getCategories()

    # Go thru each category and get all the items associated to it.
    result = []
    for category in categories:
        cat_json = category.serialize

        # Query items by category id
        items = getItemsByCategoryId(cid=category.id)
        category_items = []
        for item in items:
            # Collect all items in json
            category_items.append(item.serialize)

        # Modify the category json to add the item json to it.
        cat_json['Item'] = category_items

        result.append(cat_json)

    return jsonify(Category=result)


@app.route('/')
@app.route('/catalog')
def listCatalogsAndLatestItems():
    categories = getCategories()
    items = getLatestItems()
    item_title = 'Latest Items'

    return render_template(
        'main.html', categories=categories, items=items, item_title=item_title)

# Catalog


@app.route('/catalog/addcategory', methods=['GET', 'POST'])
def addCategory():
    # Check Authentication
    if 'username' not in login_session:
        flash("You must be a logged in to add category")
        return redirectHome()
    else:
        if request.method == 'POST':
            name = request.form['name']

            # Check if its not null
            if len(name) == 0:
                return render_template('addcategory.html',
                                       page_title='Add Category',
                                       name=name,
                                       error='Category name must not be empty.')
            else:
                # Check if the category exists
                categoryToUse = getCategoryByName(name=name)
                if categoryToUse is not None:
                    return render_template('addcategory.html',
                                           page_title='Add Category',
                                           name=name,
                                           error='Category exists already.')
                else:
                    newCategory = Category(name=name, user_id=login_session['user_id'])

                    session.add(newCategory)
                    session.commit()

                    flash(
                        "'{category}' Category Successfully Created"
                        .format(category=newCategory.name))

                    return redirect(url_for('viewCategory',
                                            category=newCategory.name))
        else:
            return render_template('addcategory.html', page_title='Add Category')


@app.route('/catalog/<string:category>/items', methods=['GET', 'POST'])
def viewCategory(category):
    categoryToUse = getCategoryByName(name=category)
    if categoryToUse is not None:
        category_id = categoryToUse.id
        categories = getCategories()
        items = getItemsByCategoryId(cid=category_id)
        item_title = "{name} Items ({count} items)".format(
            name=categoryToUse.name, count=items.count())

        return render_template('main.html',
                               categories=categories,
                               items=items,
                               selected_category=categoryToUse,
                               item_title=item_title)

    else:
        return redirectHome()


@app.route('/catalog/<string:category>/edit', methods=['GET', 'POST'])
def editCategory(category):
    # Check Authentication
    if 'username' not in login_session:
        flash("You must be a logged in to edit a category.")
        return redirectHome()
    
    # Check if category exists.
    categoryToUse = getCategoryByName(name=category)
    if categoryToUse is None:
        flash("Category does NOT exist.")
        return redirectHome()

    # Check Authorization
    if categoryToUse.user_id != login_session['user_id']:
        flash("You must be the category owner to edit it.")
        return redirectHome()

    # Proceed once it passes authentication and authorization checks.
    page_title = "Edit Category"
    if request.method == 'POST':
        name = request.form['name']
        category_id = int(request.form['category_id'])

        # Check if its not null
        if len(name) == 0:
            return render_template('editcategory.html',
                                   page_title=page_title,
                                   name=name,
                                   category_id=categoryToUse.id,
                                   error='Category name is empty.')
        else:
            categoryToUse = getCategoryById(cid=category_id)

            categoryToUse.name = name

            flash(
                "'{category}' Category Successfully Edited"
                .format(category=name))

            return redirect(url_for('viewCategory',
                                    category=categoryToUse.name))
    else:
        return render_template('editcategory.html',
                               page_title=page_title,
                               name=category,
                               category_id=categoryToUse.id)


@app.route('/catalog/<string:category>/delete', methods=['GET', 'POST'])
def deleteCategory(category):
    # Check Authentication
    if 'username' not in login_session:
        flash("You must be a logged in to delete a category")
        return redirectHome()

    # Check if category exists
    categoryToUse = getCategoryByName(name=category)
    if categoryToUse is None:
        flash("Category does NOT exist.")
        return redirectHome()

    # Check Authorization
    if categoryToUse.user_id != login_session['user_id']:
        flash("You must be the category owner to delete it.")
        return redirectHome()

    # Proceed once it passes authentication and authorization checks.
    if request.method == 'POST':
        categoryName = categoryToUse.name
        
        # Delete all items associated with this category
        deleteItemsByCategoryId(categoryToUse.id)

        # Delete the category
        session.delete(categoryToUse)
        session.commit()

        flash(
            "'{category}' Category Successfully Deleted"
            .format(category=categoryName))

        return redirectHome()
    else:
        return render_template('deleteCategory.html', category=category)


# Item


@app.route('/catalog/additem', methods=['GET', 'POST'])
def addItem():
    # Check Authentication
    if 'username' not in login_session:
        flash("You must be a logged in to add an item")
        return redirectHome()
    else:
        page_title = 'Add Item'
        categories = getCategories()

        if request.method == 'POST':
            item_title = request.form['item_title']
            item_description = request.form['item_description']
            category_id = int(request.form['category_id'])
            error = ""

            if len(item_title) > 0 and len(item_description) > 0\
                    and category_id > 0:
                # Ensure the item doesn't exist already
                itemToUse = getItem(title=item_title, cid=category_id)
                categoryToUse = getCategoryById(cid=category_id)
                if itemToUse is not None:
                    error = "'{item_title}' already exists under '{category}' Category".\
                                                format(item_title=item_title,
                                                        category=categoryToUse.name)
                    return render_template('additem.html',
                                           page_title=page_title,
                                           error=error,
                                           item_title=item_title,
                                           item_description=item_description,
                                           category_id=category_id,
                                           category=None,
                                           categories=categories)
                else:
                    newItem = Item(title=item_title,
                                   description=item_description,
                                   category_id=category_id,
                                   user_id=login_session['user_id'])

                    session.add(newItem)

                    flash(
                        "'{item}' Item Successfully Created"
                        .format(item=newItem.title))

                    session.commit()

                    return redirect(url_for('viewCategory',
                                            category=categoryToUse.name))
            else:
                if len(item_title) == 0:
                    error = 'Please provide a title.'
                elif len(item_description) == 0:
                    error = 'Please provide a description.'
                elif category_id == -1:
                    error = 'Please select a category.'

                return render_template('additem.html',
                                       page_title=page_title,
                                       error=error,
                                       item_title=item_title,
                                       item_description=item_description,
                                       category_id=category_id,
                                       category=None,
                                       categories=categories)
        else:
            # Display the drop down list and let user pick the category
            categories = getCategories()
            return render_template('additem.html',
                                   page_title=page_title,
                                   category=None,
                                   categories=categories)


@app.route('/catalog/<string:category>/add', methods=['GET', 'POST'])
def addItemToCategory(category):
    # Check Authentication
    if 'username' not in login_session:
        flash("You must be logged in to add an item")
        return redirectHome()
    else:
        categoryToUse = getCategoryByName(name=category)
        if categoryToUse is not None:
            page_title = "Add new item to '{category}' category".format(
                category=categoryToUse.name)
            if request.method == 'POST':
                item_title = request.form['item_title']
                item_description = request.form['item_description']
                category_id = request.form['category_id']
                error = ""

                if len(item_title) > 0 and len(item_description) > 0\
                        and category_id > 0:
                    # Ensure the item doesn't exist already
                    itemToUse = getItem(title=item_title, cid=category_id)
                    if itemToUse is not None:
                        error = "'{item}' already exists in '{category}'"\
                                .format(item=item_title,
                                        category=categoryToUse.name)
                        return render_template('additem.html',
                                               page_title=page_title,
                                               error=error,
                                               item_title=item_title,
                                               item_description=item_description,
                                               category_id=category_id,
                                               category=categoryToUse,
                                               categories=None)
                    else:
                        newItem = Item(title=item_title,
                                       description=item_description,
                                       category_id=categoryToUse.id,
                                       user_id=login_session['user_id'])

                        session.add(newItem)

                        flash(
                            "'{item}' Item Successfully Created in '{category}'"
                            .format(item=item_title, category=categoryToUse.name))

                        session.commit()

                        return redirect(url_for('viewCategory',
                                                category=categoryToUse.name))
                else:
                    if len(item_title) == 0:
                        error = 'Please provide a title.'
                    elif len(item_description) == 0:
                        error = 'Please provide a description.'

                    return render_template('additem.html',
                                           page_title=page_title,
                                           item_title=item_title,
                                           item_description=item_description,
                                           category=categoryToUse,
                                           categories=None,
                                           error=error)
            else:
                # Display the drop down list and let user pick the category
                return render_template('additem.html',
                                       page_title=page_title,
                                       category=categoryToUse,
                                       categories=None)
        else:
            return redirectHome()


@app.route('/catalog/<string:category>/<string:item>', methods=['GET', 'POST'])
def viewItem(category, item):
    categoryToUse = getCategoryByName(name=category)
    if categoryToUse is not None:
        category_id = categoryToUse.id
        itemToUse = getItem(title=item, cid=category_id)
        if itemToUse is not None:
            return render_template('viewitem.html',
                                   itemToUse=itemToUse,
                                   category=category,
                                   item=item)
        else:
            return "Error encountered for category:{category} " +\
                "and item:{item}".format(cid=category_id,
                                         category=category,
                                         item=item)
    else:
        return redirectHome()


@app.route('/catalog/<string:category>/<string:item>/edit',
           methods=['GET', 'POST'])
def editItem(category, item):
    # Check Authentication
    if 'username' not in login_session:
        flash("You must be a logged in to edit an item")
        return redirectHome()

    # Check if category exists
    categoryToUse = getCategoryByName(name=category)
    if categoryToUse is None:
        flash("Category does NOT exist.")
        return redirectHome()

    # Check if item exists
    itemToUse = getItem(title=item, cid=categoryToUse.id)
    if itemToUse is None:
        flash("Item does NOT exist.")
        return redirectHome()

    # Check Authorization
    if categoryToUse.user_id != login_session['user_id']:
        flash("You must be the item owner to edit it.")
        return redirectHome()

    # Proceed once it passes authentication and authorization.
    categories = getCategories()
    page_title = 'Edit Item'

    if request.method == 'POST':
        item_title = request.form['item_title']
        item_description = request.form['item_description']
        item_id = request.form['item_id']
        category_id = int(request.form['category_id'])
        itemToUse = getItemById(iid=item_id)

        if len(item_title) > 0 and len(item_description) > 0:
            itemToUse.title = item_title
            itemToUse.description = item_description
            itemToUse.category_id = category_id
            itemToUse.timestamp = datetime.utcnow()

            # Get the name of the category
            categoryToUse = getCategoryById(cid=category_id)

            flash(
                "'{item}' Item Successfully Edited in '{category}'"
                .format(item=itemToUse.title, category=categoryToUse.name))

            return redirect(url_for('viewItem',
                                    category=categoryToUse.name,
                                    item=item_title))
        else:
            if len(item_title) == 0:
                error = 'Please provide a title.'
            elif len(item_description) == 0:
                error = 'Please provide a description.'

            return render_template('edititem.html',
                                   page_title=page_title,
                                   error=error,
                                   item_title=itemToUse.title,
                                   item_description=itemToUse.description,
                                   item_id=itemToUse.id,
                                   categories=categories)

    else:
        category_id = categoryToUse.id
        itemToUse = getItem(title=item, cid=category_id)

        return render_template('edititem.html',
                               page_title=page_title,
                               item_title=itemToUse.title,
                               item_description=itemToUse.description,
                               item_id=itemToUse.id,
                               categories=categories,
                               category_id=category_id)


@app.route('/catalog/<string:category>/<string:item>/delete',
           methods=['GET', 'POST'])
def deleteItem(category, item):
    # Check Authentication
    if 'username' not in login_session:
        flash("You must be logged in to delete an item")
        return redirectHome()

    # Check if category exists
    categoryToUse = getCategoryByName(name=category)
    if categoryToUse is None:
        flash("Category does NOT exist.")
        return redirectHome()

    # Check if item exists
    itemToUse = getItem(title=item, cid=categoryToUse.id)
    if itemToUse is None:
        flash("Item does NOT exist.")
        return redirectHome()

    # Check Authorization
    if itemToUse.user_id != login_session['user_id']:
        flash("You must be the item owner to delete it.")
        return redirectHome()

    # Proceed once it passes authentication and authorization.
    category_id = categoryToUse.id
    itemToUse = getItem(title=item, cid=category_id)
    if request.method == 'POST':
        deletedItemTitle = itemToUse.title
        session.delete(itemToUse)
        session.commit()

        flash(
            "'{item}' Item Successfully Deleted"
            .format(item=deletedItemTitle))

        return redirect(url_for('viewCategory',
                                category=categoryToUse.name))
    else:
        return render_template('deleteItem.html', item_title=item)



# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirectHome()
    else:
        flash("You were not logged in")
        return redirectHome()


if __name__ == '__main__':
    app.secret_key = 'my_catalog_app_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
