from flask import Flask, render_template, request, redirect, jsonify, \
                  url_for, flash
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item
from datetime import datetime

import json

app = Flask(__name__)

engine = create_engine('sqlite:///catalogwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

LATEST_ITEMS_TO_DISPLAY_COUNT = 8

# Helper functions


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


def getLatestItems():
    try:
        return session.query(Item).order_by(desc(Item.timestamp))\
                                  .limit(LATEST_ITEMS_TO_DISPLAY_COUNT)
    except:
        return None


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
                # HACK: Replace user_id with correct user id.
                newCategory = Category(name=name, user_id=1)

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
        return redirect(url_for('listCatalogsAndLatestItems'))


@app.route('/catalog/<string:category>/edit', methods=['GET', 'POST'])
def editCategory(category):
    categoryToUse = getCategoryByName(name=category)
    page_title = "Edit Category"
    if categoryToUse is not None:
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
    else:
        return redirect(url_for('listCatalogsAndLatestItems'))


@app.route('/catalog/<string:category>/delete', methods=['GET', 'POST'])
def deleteCategory(category):
    categoryToUse = getCategoryByName(name=category)
    if categoryToUse is not None:
        if request.method == 'POST':
            categoryName = categoryToUse.name
            session.delete(categoryToUse)
            session.commit()

            flash(
                "'{category}' Category Successfully Deleted"
                .format(category=categoryName))

            return redirect(url_for('listCatalogsAndLatestItems'))
        else:
            return render_template('deleteCategory.html', category=category)

    else:
        return redirect(url_for('listCatalogsAndLatestItems'))

# Item


@app.route('/catalog/additem', methods=['GET', 'POST'])
def addItem():
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
                error = "'{item_title}' already exists under '{category}'" +\
                        " Category".format(item_title=item_title,
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
                # HACK: Replace user_id with correct user id.
                newItem = Item(title=item_title,
                               description=item_description,
                               category_id=category_id,
                               user_id=1)

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
                    # HACK: Replace user_id with correct user id.
                    newItem = Item(title=item_title,
                                   description=item_description,
                                   category_id=categoryToUse.id,
                                   user_id=1)

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
        return redirect(url_for('listCatalogsAndLatestItems'))


@app.route('/catalog/<string:category>/<string:item>', methods=['GET', 'POST'])
def viewItem(category, item):
    categoryToUse = getCategoryByName(name=category)
    if categoryToUse is not None:
        category_id = categoryToUse.id
        itemToUse = getItem(title=item, cid=category_id)
        if itemToUse is not None:
            return render_template('viewitem.html',
                                   title=itemToUse.title,
                                   description=itemToUse.description,
                                   category=category,
                                   item=item)
        else:
            return "Error encountered for category:{category} " +\
                "and item:{item}".format(cid=category_id,
                                         category=category,
                                         item=item)
    else:
        return redirect(url_for('listCatalogsAndLatestItems'))


@app.route('/catalog/<string:category>/<string:item>/edit',
           methods=['GET', 'POST'])
def editItem(category, item):
    categoryToUse = getCategoryByName(name=category)
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
        if categoryToUse is not None:
            category_id = categoryToUse.id
            itemToUse = getItem(title=item, cid=category_id)

            return render_template('edititem.html',
                                   page_title=page_title,
                                   item_title=itemToUse.title,
                                   item_description=itemToUse.description,
                                   item_id=itemToUse.id,
                                   categories=categories,
                                   category_id=category_id)

        else:
            return redirect(url_for('listCatalogsAndLatestItems'))


@app.route('/catalog/<string:category>/<string:item>/delete',
           methods=['GET', 'POST'])
def deleteItem(category, item):
    categoryToUse = getCategoryByName(name=category)
    if categoryToUse is not None:
        category_id = categoryToUse.id
        itemToUse = getItem(title=item, cid=category_id)
        if itemToUse is not None:
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
        else:
            return redirect(url_for('listCatalogsAndLatestItems'))
    else:
        return redirect(url_for('listCatalogsAndLatestItems'))

if __name__ == '__main__':
    app.secret_key = 'my_catalog_app_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
