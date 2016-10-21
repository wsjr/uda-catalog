Catalog App
=============
The catalog app is designed to display categories and items created by
logged in users. A user has an option of logging in using his/her **Google Plus** or
**Facebook** account. Only a logged user can edit/delete his or her own category
and item. 

This app is built using:

 - Twitter Bootstrap
 - FontAwesome
 - SQLAlchemy + SQLite
 - Flask
 - oAuths (Google Plus and Facebook)

----


How To Use?
=============
Before starting, navigate to ***models*** folder and remove ***catalogwithusers.db***, if there's any, to ensure we have a clean database.
> cd models

> rm catalogwithusers.db

Populate the database with preset entries
> python populatecatalog.py

Go up one level and run **project.py**
> cd ..

> python project.py

Finally, once the server is running, you can access the catalog app by navigating to:
> http://localhost:5000/

 or
  
> http://localhost:5000/catalog/

In addition, There are several JSON API exposed to get data:

- To view all the categories and items:
> http://localhost:5000/catalog/json

- To view a particular category:
> http://localhost:5000/catalog/[string:category]/json
> 
> For example, to get the JSON data for **Soccer** category
> 
> http://localhost:5000/catalog/Soccer/json

- To view a particular item in a category:
> http://localhost:5000/catalog/[string:category]/[string:item]/json
> 
> For example, to get the JSON data for **Padding** item in **Soccer** category
> 
> http://localhost:5000/catalog/Soccer/Padding/json


What features are available?
==============
As a logged in user:

 - You can add categories.
 - You can edit and delete categories that you have created.
 - You can add items.
 - You can edit and delete items that you have created.
 
As a logged out user:

 - You can only view categories and items.

