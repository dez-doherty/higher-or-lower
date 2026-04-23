from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone
from typing import Optional
from hashlib import md5
import enum

import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db, login
from flask_login import UserMixin


# =========================
# ENUM
# =========================

class CollectionCategory(enum.Enum):
    sports = "sports"
    games = "games"
    movies = "movies"
    music = "music"
    science = "science"


# =========================
# USER
# =========================

followers = sa.Table(
    'followers',
    db.metadata,
    sa.Column('follower_id', sa.Integer, sa.ForeignKey('user.id'),
            primary_key=True),
    sa.Column('followed_id', sa.Integer, sa.ForeignKey('user.id'),
            primary_key=True)
    )
    
class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    username: so.Mapped[str] = so.mapped_column(
        sa.String(50), index=True, unique=True, nullable=False
    )

    email: so.Mapped[str] = so.mapped_column(
        sa.String(120), index=True, unique=True, nullable=False
    )

    password_hash: so.Mapped[str] = so.mapped_column(
        sa.String(256), nullable=False, default=''
    )

    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    collections: so.WriteOnlyMapped['Collection'] = so.relationship(
        back_populates='creator', passive_deletes=True
    )

    leaderboards: so.WriteOnlyMapped['Leaderboard'] = so.relationship(
        back_populates='user', passive_deletes=True
    )

    favourites: so.WriteOnlyMapped['Favourite'] = so.relationship(
        back_populates='user', passive_deletes=True
    )

    collection_history: so.WriteOnlyMapped['CollectionHistory'] = so.relationship(
        back_populates='user', passive_deletes=True
    )
    
    following: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        back_populates='followers')
    
    followers: so.WriteOnlyMapped['User'] = so.relationship(
        secondary=followers, primaryjoin=(followers.c.followed_id == id),
        secondaryjoin=(followers.c.follower_id == id),
        back_populates='following')


    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'
    
    
    def follow(self, user):
        if not self.is_following(user):
            self.following.add(user)

    def unfollow(self, user):
        if self.is_following(user):
            self.following.remove(user)

    def is_following(self, user):
        query = self.following.select().where(User.id == user.id)
        return db.session.scalar(query) is not None

    def followers_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.followers.select().subquery())
        return db.session.scalar(query)

    def following_count(self):
        query = sa.select(sa.func.count()).select_from(
            self.following.select().subquery())
        return db.session.scalar(query)
    

    def following_collections(self):
        Author = so.aliased(User)
        Follower = so.aliased(User)
        return (
            sa.select(Collection)
            .join(Collection.creator.of_type(Author))
            .join(Author.followers.of_type(Follower), isouter=True)
            .where(sa.or_(
                Follower.id == self.id,
                Author.id == self.id,
            ))
            .group_by(Collection)
            .order_by(Collection.name)
        )

# =========================
# COLLECTION
# =========================

class Collection(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    name: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False)

    image: so.Mapped[Optional[str]] = so.mapped_column(sa.String(255))

    creator_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey(User.id), nullable=False
    )

    category: so.Mapped[CollectionCategory] = so.mapped_column(
        sa.Enum(CollectionCategory), nullable=False
    )

    creator: so.Mapped[User] = so.relationship(back_populates='collections')

    items: so.WriteOnlyMapped['Item'] = so.relationship(
        back_populates='collection', passive_deletes=True
    )

    leaderboards: so.WriteOnlyMapped['Leaderboard'] = so.relationship(
        back_populates='collection', passive_deletes=True
    )

    favourites: so.WriteOnlyMapped['Favourite'] = so.relationship(
        back_populates='collection', passive_deletes=True
    )

    history: so.WriteOnlyMapped['CollectionHistory'] = so.relationship(
        back_populates='collection', passive_deletes=True
    )

    def __repr__(self):
        return f'<Collection {self.name}>'


# =========================
# ITEM
# =========================

class Item(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    collection_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey(Collection.id), nullable=False
    )

    name: so.Mapped[str] = so.mapped_column(sa.String(100), nullable=False)

    value: so.Mapped[int] = so.mapped_column(nullable=False)

    image: so.Mapped[Optional[str]] = so.mapped_column(sa.String(255))

    collection: so.Mapped[Collection] = so.relationship(back_populates='items')

    def __repr__(self):
        return f'<Item {self.name}>'


# =========================
# LEADERBOARD
# =========================

class Leaderboard(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    user_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey(User.id), nullable=False
    )

    collection_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey(Collection.id), nullable=False
    )

    score: so.Mapped[int] = so.mapped_column(nullable=False)

    played_at: so.Mapped[datetime] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    user: so.Mapped[User] = so.relationship(back_populates='leaderboards')

    collection: so.Mapped[Collection] = so.relationship(back_populates='leaderboards')

    def __repr__(self):
        return f'<Leaderboard {self.user_id} {self.score}>'


# =========================
# FAVOURITE
# =========================

class Favourite(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    user_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey(User.id), nullable=False
    )

    collection_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey(Collection.id), nullable=False
    )

    user: so.Mapped[User] = so.relationship(back_populates='favourites')

    collection: so.Mapped[Collection] = so.relationship(back_populates='favourites')

    def __repr__(self):
        return f'<Favourite {self.user_id} {self.collection_id}>'


# =========================
# COLLECTION HISTORY
# =========================

class CollectionHistory(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)

    user_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey(User.id), nullable=False
    )

    collection_id: so.Mapped[int] = so.mapped_column(
        sa.ForeignKey(Collection.id), nullable=False
    )

    played_at: so.Mapped[datetime] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    user: so.Mapped[User] = so.relationship(back_populates='collection_history')

    collection: so.Mapped[Collection] = so.relationship(back_populates='history')

    def __repr__(self):
        return f'<CollectionHistory {self.user_id} {self.collection_id}>'


# =========================
# LOGIN LOADER
# =========================

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))