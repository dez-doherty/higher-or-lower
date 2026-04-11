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

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'


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