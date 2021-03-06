import os
import datetime
from peewee import *
from playhouse.migrate import *

db_proxy = Proxy()

if "HEROKU" in os.environ:
    import urlparse
    import psycopg2

    urlparse.uses_netloc.append("postgres")
    url = urlparse.urlparse(os.environ["DATABASE_URL"])
    db = PostgresqlDatabase(database=url.path[1:], user=url.username,
                            password=url.password, host=url.hostname,
                            port=url.port)
    db_proxy.initialize(db)
    migrator = PostgresqlMigrator(db_proxy)
else:
    db = SqliteDatabase('fifpro.db')
    # Initializing database with proxy
    db_proxy.initialize(db)
    migrator = SqliteMigrator(db_proxy)


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    username = CharField(unique=True)
    password = CharField()
    matches_played = IntegerField(default=0)
    is_moderater = BooleanField(default=False)
    join_date = DateTimeField(default=datetime.datetime.now)


class Match(BaseModel):
    player1 = ForeignKeyField(User, related_name='player1')
    player2 = ForeignKeyField(User, related_name='player2')
    player1_goals = IntegerField(default=0)
    player2_goals = IntegerField(default=0)
    pub_date = DateTimeField(default=datetime.datetime.now)


class CachedYelpPlace(BaseModel):
    """
    This Model will be tightly integrated with memcache to cut down extensive
    api calls to yelp
    """
    yelp_id = CharField(unique=True, index=True)
    yelp_data = CharField()
    pub_date = DateTimeField(default=datetime.datetime.now)


class Wager(BaseModel):
    initiator = ForeignKeyField(User, related_name='initiator')
    opponent = ForeignKeyField(User, related_name='opponent')
    yelp_id = ForeignKeyField(CachedYelpPlace)
    match = ForeignKeyField(Match, null=True, related_name="wager_match")
    pub_date = DateTimeField(default=datetime.datetime.now)


def init_db():
    db.create_tables([User, Match, CachedYelpPlace, Wager],
                     safe=True)


def migrations():
    """
    Runs all needed database migrations
    """
    migrate(
        migrator.add_column("wager", "match", ForeignKeyField(Match, related_name="match", null=True))
    )


# This file is only run when we need to create our tables in Heroku Postgres.
if __name__ == "__main__":
    db_proxy.connect()
    # Create tables if not created
    init_db()
    db_proxy.close()
