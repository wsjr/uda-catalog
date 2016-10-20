from database_setup import Base, Category, Item, User


from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker


LATEST_ITEMS_TO_DISPLAY_COUNT = 8

engine = create_engine('sqlite:///models//catalogwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


class Categories(object):

    """
    Categories Model
    """
    @classmethod
    def create_entry(self, name, uid):
        newCategory = Category(name=name, user_id=uid)
        session.add(newCategory)
        session.commit()
        return newCategory

    @classmethod
    def by_name(self, name):
        try:
            return session.query(Category).filter_by(name=name).one()
        except:
            return None

    @classmethod
    def by_id(self, cid):
        try:
            return session.query(Category).filter_by(id=cid).one()
        except:
            return None

    @classmethod
    def get_all(self):
        try:
            return session.query(Category).all()
        except:
            return None

    @classmethod
    def remove(self, category):
        session.delete(category)
        session.commit()


class Items(object):

    """
    Items Model
    """
    @classmethod
    def create_entry(self, title, description, cid, uid):
        newItem = Item(title=title,
                       description=description,
                       category_id=cid,
                       user_id=uid)

        session.add(newItem)
        session.commit()
        return newItem

    @classmethod
    def by_id(self, iid):
        try:
            return session.query(Item).filter_by(id=iid).one()
        except:
            return None

    @classmethod
    def by_title_and_cid(self, title, cid):
        try:
            return session.query(Item).filter_by(title=title)\
                .filter_by(category_id=cid)\
                .one()
        except:
            return None

    @classmethod
    def by_category_id(self, cid):
        try:
            return session.query(Item).order_by(desc(Item.timestamp))\
                                      .filter_by(category_id=cid)
        except:
            return None

    @classmethod
    def remove_by_category_id(self, cid):
        try:
            session.query(Item).filter_by(category_id=cid).delete()
            session.commit()
        except:
            return None

    @classmethod
    def remove(self, item):
        session.delete(item)
        session.commit()

    @classmethod
    def get_latest_items(self):
        try:
            return session.query(Item).order_by(desc(Item.timestamp))\
                                      .limit(LATEST_ITEMS_TO_DISPLAY_COUNT)
        except:
            return None


class Users(object):

    """
    Users Model
    """
    @classmethod
    def create_entry(self, username, email, picture):
        newUser = User(name=username, email=email, picture=picture)
        session.add(newUser)
        session.commit()
        user = session.query(User).filter_by(email=email).one()

        return user.id

    @classmethod
    def user_info(self, uid):
        user = session.query(User).filter_by(id=uid).one()
        return user

    @classmethod
    def get_user_id(self, email):
        try:
            user = session.query(User).filter_by(email=email).one()
            return user.id
        except:
            return None
