from app import app, db
import sqlalchemy as sa
import sqlalchemy.orm as so
from app.models import User, Collection, CollectionCategory, Item, Leaderboard, Favourite, CollectionHistory

with app.app_context():
    db.create_all()

@app.shell_context_processor
def make_shell_context():
    return {
        'sa': sa,
        'so': so,
        'db': db,
        'User': User,
        'Collection': Collection,
        'Item': Item,
        'Leaderboard': Leaderboard,
        'Favourite': Favourite,
        'CollectionHistory': CollectionHistory
    }

with app.app_context():
    db.create_all()
    if User.query.count() == 0:
        u = User(username='john', email='john@example.com')
        u.set_password('mypassword')
        db.session.add(u)
        db.session.commit()

    john = db.session.scalar(sa.select(User).where(User.username == 'john'))
    if john and not db.session.scalar(
        sa.select(Collection).where(Collection.creator_id == john.id)
    ):
        c = Collection(
            name='Premier League Clubs',
            category=CollectionCategory.sports,
            creator_id=john.id,
        )
        db.session.add(c)
        db.session.flush()
        db.session.add_all([
            Item(collection_id=c.id, name='Manchester City', value=115),
            Item(collection_id=c.id, name='Arsenal', value=89),
            Item(collection_id=c.id, name='Liverpool', value=82),
            Item(collection_id=c.id, name='Chelsea', value=63),
            Item(collection_id=c.id, name='Tottenham', value=60),
        ])
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, port=5001)
