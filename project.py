from flask import Flask, render_template, request, redirect, jsonify, \
    url_for, flash
from flask import session as login_session
from datetime import datetime
import random
import string

from models import model
from auths import fbauth, gpauth


app = Flask(__name__)

APPLICATION_NAME = "Catalog Application"


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
    output = fbauth.Authentication.connect()
    return output


@app.route('/fbdisconnect')
def fbdisconnect():
    output = fbauth.Authentication.disconnect()
    return output


@app.route('/gconnect', methods=['POST'])
def gconnect():
    output = gpauth.Authentication.connect()
    return output


@app.route('/gdisconnect')
def gdisconnect():
    output = gpauth.Authentication.disconnect()
    return output


def redirectHome():
    return redirect(url_for('listCatalogsAndLatestItems'))


# JSON ENDPOINT
@app.route('/catalog.json')
def getJSON():
    # Get all categories
    lCategories = model.Categories.get_all()

    # Go thru each category and get all the items associated to it.
    result = []
    for category in lCategories:
        cat_json = category.serialize

        # Query items by category id
        items = model.Items.by_category_id(cid=category.id)
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
    lCategories = model.Categories.get_all()
    lItems = model.Items.get_latest_items()

    item_title = 'Latest Items'

    return render_template('main.html',
                           categories=lCategories,
                           items=lItems,
                           item_title=item_title)

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
                                       error='Category must not be empty.')
            else:
                # Check if the category exists
                categoryToUse = model.Categories.by_name(name=name)
                if categoryToUse is not None:
                    return render_template('addcategory.html',
                                           page_title='Add Category',
                                           name=name,
                                           error='Category exists already.')
                else:
                    newCategory = model.Categories.create_entry(
                        name=name, uid=login_session['user_id'])

                    flash(
                        "'{category}' Category Successfully Created"
                        .format(category=newCategory.name))

                    return redirect(url_for('viewCategory',
                                            category=newCategory.name))
        else:
            return render_template('addcategory.html',
                                   page_title='Add Category')


@app.route('/catalog/<string:category>/items', methods=['GET', 'POST'])
def viewCategory(category):
    categoryToUse = model.Categories.by_name(name=category)
    if categoryToUse is not None:
        category_id = categoryToUse.id
        lCategories = model.Categories.get_all()
        lItems = model.Items.by_category_id(cid=category_id)
        item_title = "{name} Items ({count} items)".format(
            name=categoryToUse.name, count=lItems.count())

        return render_template('main.html',
                               categories=lCategories,
                               items=lItems,
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
    categoryToUse = model.Categories.by_name(name=category)
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
            categoryToUse = model.Categories.by_id(cid=category_id)
            categoryToUse.name = name

            flash(
                "'{category}' Category Successfully Edited"
                .format(category=name))

            return redirect(url_for('viewCategory',
                                    category=categoryToUse.name))
    else:
        return render_template('editcategory.html',
                               page_title=page_title,
                               name=categoryToUse.name,
                               category_id=categoryToUse.id)


@app.route('/catalog/<string:category>/delete', methods=['GET', 'POST'])
def deleteCategory(category):
    # Check Authentication
    if 'username' not in login_session:
        flash("You must be a logged in to delete a category")
        return redirectHome()

    # Check if category exists
    categoryToUse = model.Categories.by_name(name=category)
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
        model.Items.remove_by_category_id(categoryToUse.id)

        # Delete the category
        model.Categories.remove(category=categoryToUse)

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
        lCategories = model.Categories.get_all()

        if request.method == 'POST':
            item_title = request.form['item_title']
            item_description = request.form['item_description']
            category_id = int(request.form['category_id'])
            error = ""

            if len(item_title) > 0 and len(item_description) > 0\
                    and category_id > 0:
                # Ensure the item doesn't exist already
                itemToUse = model.Items.by_title_and_cid(
                    title=item_title, cid=category_id)
                categoryToUse = model.Categories.by_id(cid=category_id)
                if itemToUse is not None:
                    error = "'{i}' already exists under '{c}' Category".\
                        format(i=item_title,
                               c=categoryToUse.name)
                    return render_template('additem.html',
                                           page_title=page_title,
                                           error=error,
                                           item_title=item_title,
                                           item_description=item_description,
                                           category_id=category_id,
                                           category=None,
                                           categories=lCategories)
                else:
                    newItem = model.Items.create_entry(
                        title=item_title,
                        description=item_description,
                        cid=category_id,
                        uid=login_session['user_id'])

                    flash(
                        "'{item}' Item Successfully Created"
                        .format(item=newItem.title))

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
                                       categories=lCategories)
        else:
            # Display the drop down list and let user pick the category
            lCategories = model.Categories.get_all()
            return render_template('additem.html',
                                   page_title=page_title,
                                   category=None,
                                   categories=lCategories)


@app.route('/catalog/<string:category>/add', methods=['GET', 'POST'])
def addItemToCategory(category):
    # Check Authentication
    if 'username' not in login_session:
        flash("You must be logged in to add an item")
        return redirectHome()
    else:
        categoryToUse = model.Categories.by_name(name=category)
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
                    itemToUse = model.Items.by_title_and_cid(
                        title=item_title, cid=category_id)
                    if itemToUse is not None:
                        error = "'{item}' already exists in '{category}'"\
                                .format(item=item_title,
                                        category=categoryToUse.name)
                        return render_template(
                            'additem.html',
                            page_title=page_title,
                            error=error,
                            item_title=item_title,
                            item_description=item_description,
                            category_id=category_id,
                            category=categoryToUse,
                            categories=None)
                    else:
                        model.Items.create_entry(title=item_title,
                                                 description=item_description,
                                                 cid=categoryToUse.id,
                                                 uid=login_session['user_id'])

                        flash(
                            "'{i}' Item Successfully Created in '{c}'"
                            .format(i=item_title, c=categoryToUse.name))

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
    categoryToUse = model.Categories.by_name(name=category)
    if categoryToUse is not None:
        category_id = categoryToUse.id
        itemToUse = model.Items.by_title_and_cid(title=item, cid=category_id)
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
    categoryToUse = model.Categories.by_name(name=category)
    if categoryToUse is None:
        flash("Category does NOT exist.")
        return redirectHome()

    # Check if item exists
    itemToUse = model.Items.by_title_and_cid(title=item, cid=categoryToUse.id)
    if itemToUse is None:
        flash("Item does NOT exist.")
        return redirectHome()

    # Check Authorization
    if itemToUse.user_id != login_session['user_id']:
        flash("You must be the item owner to edit it.")
        return redirectHome()

    # Proceed once it passes authentication and authorization.
    lCategories = model.Categories.get_all()
    page_title = 'Edit Item'

    if request.method == 'POST':
        item_title = request.form['item_title']
        item_description = request.form['item_description']
        item_id = request.form['item_id']
        category_id = int(request.form['category_id'])
        itemToUse = model.Items.by_id(iid=item_id)

        if len(item_title) > 0 and len(item_description) > 0:
            itemToUse.title = item_title
            itemToUse.description = item_description
            itemToUse.category_id = category_id
            itemToUse.timestamp = datetime.utcnow()

            # Get the name of the category
            categoryToUse = model.Categories.by_id(cid=category_id)

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
                                   categories=lCategories)

    else:
        category_id = categoryToUse.id
        itemToUse = model.Items.by_title_and_cid(title=item, cid=category_id)

        return render_template('edititem.html',
                               page_title=page_title,
                               item_title=itemToUse.title,
                               item_description=itemToUse.description,
                               item_id=itemToUse.id,
                               categories=lCategories,
                               category_id=category_id)


@app.route('/catalog/<string:category>/<string:item>/delete',
           methods=['GET', 'POST'])
def deleteItem(category, item):
    # Check Authentication
    if 'username' not in login_session:
        flash("You must be logged in to delete an item")
        return redirectHome()

    # Check if category exists
    categoryToUse = model.Categories.by_name(name=category)
    if categoryToUse is None:
        flash("Category does NOT exist.")
        return redirectHome()

    # Check if item exists
    itemToUse = model.Items.by_title_and_cid(title=item, cid=categoryToUse.id)
    if itemToUse is None:
        flash("Item does NOT exist.")
        return redirectHome()

    # Check Authorization
    if itemToUse.user_id != login_session['user_id']:
        flash("You must be the item owner to delete it.")
        return redirectHome()

    # Proceed once it passes authentication and authorization.
    category_id = categoryToUse.id
    if request.method == 'POST':
        deletedItemTitle = itemToUse.title
        model.Items.remove(itemToUse)

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
