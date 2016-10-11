from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Category, Item, User

from datetime import datetime

engine = create_engine('sqlite:///catalogwithusers.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user 1
user1 = User(name="User1", 
             email="user1@gmail.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(user1)
session.commit()

# Soccer Category
category1 = Category(user_id=1, name="Soccer", timestamp=datetime.utcnow())

session.add(category1)
session.commit()

# Soccer items
item1 = Item(title="Soccer Item1", 
             description="This is Soccer Item 1", 
             timestamp=datetime.utcnow(), 
             user_id=1, 
             category_id=1,
             user=user1,
             category=category1)
session.add(item1)
session.commit()

item2 = Item(title="Soccer Item2", 
             description="This is Soccer Item 2", 
             timestamp=datetime.utcnow(), 
             user_id=1, 
             category_id=1,
             user=user1,
             category=category1)
session.add(item2)
session.commit()

# Basketball Category
category2 = Category(user_id=1, name="Basketball", timestamp=datetime.utcnow())

session.add(category2)
session.commit()

# Basketball items
item1 = Item(title="Basketball Item1", 
             description="This is Basketball Item 1", 
             timestamp=datetime.utcnow(), 
             user_id=1, 
             category_id=2,
             user=user1,
             category=category2)
session.add(item1)
session.commit()

item2 = Item(title="Basketball Item2", 
             description="This is Basketball Item 2", 
             timestamp=datetime.utcnow(), 
             user_id=1, 
             category_id=2,
             user=user1,
             category=category2)
session.add(item2)
session.commit()

# Baseball Category
category3 = Category(user_id=1, name="Baseball", timestamp=datetime.utcnow())

session.add(category3)
session.commit()

# Baseball items
item1 = Item(title="Baseball Item1", 
             description="This is Baseball Item 1", 
             timestamp=datetime.utcnow(), 
             user_id=1, 
             category_id=3,
             user=user1,
             category=category3)
session.add(item1)
session.commit()

item2 = Item(title="Baseball Item2", 
             description="This is Baseball Item 2", 
             timestamp=datetime.utcnow(), 
             user_id=1, 
             category_id=3,
             user=user1,
             category=category3)
session.add(item2)
session.commit()

# Baseball Category
category4 = Category(user_id=1, name="Frisbee", timestamp=datetime.utcnow())

session.add(category4)
session.commit()

# Frisbee items
item1 = Item(title="Frisbee Item1", 
             description="This is Frisbee Item 1", 
             timestamp=datetime.utcnow(), 
             user_id=1, 
             category_id=4,
             user=user1,
             category=category4)
session.add(item1)
session.commit()

item2 = Item(title="Frisbee Item2", 
             description="This is Frisbee Item 2", 
             timestamp=datetime.utcnow(), 
             user_id=1, 
             category_id=4,
             user=user1,
             category=category4)
session.add(item2)
session.commit()


# Create dummy user 2
user2 = User(name="User2", 
             email="user2@gmail.com",
             picture='https://pbs.twimg.com/profile_images/2671170543/18debd694829ed78203a5a36dd364160_400x400.png')
session.add(user2)
session.commit()

# Snowboarding Category
category5 = Category(user_id=2, name="Snowboarding", timestamp=datetime.utcnow())

session.add(category5)
session.commit()

# Snowboarding items
item1 = Item(title="Snowboarding Item1", 
             description="This is Snowboarding Item 1", 
             timestamp=datetime.utcnow(), 
             user_id=2, 
             category_id=5,
             user=user2,
             category=category5)
session.add(item1)
session.commit()

item2 = Item(title="Snowboarding Item2", 
             description="This is Snowboarding Item 2", 
             timestamp=datetime.utcnow(), 
             user_id=2, 
             category_id=5,
             user=user2,
             category=category5)
session.add(item2)
session.commit()

# Rock Climbing Category
category6 = Category(user_id=2, name="Rock Climbing", timestamp=datetime.utcnow())

session.add(category6)
session.commit()

# Rock Climbing items
item1 = Item(title="Rock Climbing Item1", 
             description="This is Rock Climbing Item 1", 
             timestamp=datetime.utcnow(), 
             user_id=2, 
             category_id=6,
             user=user2,
             category=category6)
session.add(item1)
session.commit()

item2 = Item(title="Rock Climbing Item2", 
             description="This is Rock Climbing Item 2", 
             timestamp=datetime.utcnow(), 
             user_id=2, 
             category_id=6,
             user=user2,
             category=category6)
session.add(item2)
session.commit()

# Foosball Category
category7 = Category(user_id=2, name="Foosball", timestamp=datetime.utcnow())

session.add(category3)
session.commit()

# Foosball items
item1 = Item(title="Foosball Item1", 
             description="This is Foosball Item 1", 
             timestamp=datetime.utcnow(), 
             user_id=2, 
             category_id=7,
             user=user2,
             category=category7)
session.add(item1)
session.commit()

item2 = Item(title="Foosball Item2", 
             description="This is Foosball Item 2", 
             timestamp=datetime.utcnow(), 
             user_id=2, 
             category_id=7,
             user=user2,
             category=category7)
session.add(item2)
session.commit()

# Skating Category
category8 = Category(user_id=2, name="Skating", timestamp=datetime.utcnow())

session.add(category8)
session.commit()

# Frisbee items
item1 = Item(title="Skating Item1", 
             description="This is Skating Item 1", 
             timestamp=datetime.utcnow(), 
             user_id=2, 
             category_id=8,
             user=user2,
             category=category8)
session.add(item1)
session.commit()

item2 = Item(title="Skating Item2", 
             description="This is Skating Item 2", 
             timestamp=datetime.utcnow(), 
             user_id=2, 
             category_id=8,
             user=user2,
             category=category8)
session.add(item2)
session.commit()

# Hockey Category
category9 = Category(user_id=2, name="Hockey", timestamp=datetime.utcnow())

session.add(category9)
session.commit()

# Hockey items
item1 = Item(title="Hockey Item1", 
             description="This is Hockey Item 1", 
             timestamp=datetime.utcnow(), 
             user_id=2, 
             category_id=9,
             user=user2,
             category=category9)
session.add(item1)
session.commit()

item2 = Item(title="Hockey Item2", 
             description="This is Hockey Item 2", 
             timestamp=datetime.utcnow(), 
             user_id=2, 
             category_id=9,
             user=user2,
             category=category9)
session.add(item2)
session.commit()


print "added category items"