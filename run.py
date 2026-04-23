from app import app, db
import sqlalchemy as sa
import sqlalchemy.orm as so
from app.models import User, Collection, Item, Leaderboard, Favourite, CollectionHistory

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

if __name__ == '__main__':
    app.run(debug=True, port=5001)
