from flask import render_template, flash, redirect, url_for
from flask import request
from urllib.parse import urlsplit

import sqlalchemy as sa

from datetime import datetime, timezone

from app import app
from app import db
from app.models import User, Collection, CollectionCategory
from app.forms import RegistrationForm, CollectionForm

from app.forms import LoginForm
from flask_login import current_user, login_user
from flask_login import logout_user
from flask_login import login_required
from datetime import datetime, timezone

from flask import g
from app.forms import SearchForm, EmptyForm

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()
        g.search_form = SearchForm()
        
@app.route('/')
@app.route('/index')
@login_required
def index():
    form = CollectionForm()
    if form.validate_on_submit():
        collection = Collection(
            name=form.collection_name.data,
            category=CollectionCategory.sports,
            creator=current_user,
        )
        db.session.add(collection)
        db.session.commit()
        flash('Your collection is now live!')
        return redirect(url_for('index'))
    
    collections = db.session.scalars(current_user.following_collections()).all()

    page = request.args.get('page', 1, type=int)
    collections = db.paginate(current_user.following_collections(), page=page,
                        per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('index', page=collections.next_num) \
    if collections.has_next else None
    prev_url = url_for('index', page=collections.prev_num) \
    if collections.has_prev else None
    return render_template('index.html', title='Home', form=form,
                           collections=collections.items, next_url=next_url,
                           prev_url=prev_url)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')

        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')

        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    page = request.args.get('page', 1, type=int)
    query = user.collections.select().order_by(Collection.timestamp.desc())
    collections = db.paginate(query, page=page,
                              per_page=app.config['POSTS_PER_PAGE'],
                              error_out=False)
    next_url = url_for('user', username=user.username, page=collections.next_num) \
        if collections.has_next else None
    prev_url = url_for('user', username=user.username, page=collections.prev_num) \
        if collections.has_prev else None
    form = EmptyForm()
    return render_template('user.html', user=user, collections=collections.items,
                           next_url=next_url, prev_url=prev_url, form=form)

@app.route('/collection/<collection_id>')
@login_required
def collection(collection_id):
    collection = db.first_or_404(sa.select(Collection).where(Collection.id == collection_id))
    items = db.session.scalars(collection.items.select()).all()
    return render_template('collection.html', collection=collection, items=items)

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'You are following {username}!')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == username))
        if user is None:
            flash(f'User {username} not found.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot unfollow yourself!')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'You are not following {username}.')
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))

@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    query = sa.select(Collection).order_by(Collection.timestamp.desc())
    collections = db.paginate(query, page=page,
                              per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('explore', page=collections.next_num) \
        if collections.has_next else None
    prev_url = url_for('explore', page=collections.prev_num) \
        if collections.has_prev else None
    return render_template("index.html", title='Explore', collections=collections.items, next_url=next_url, prev_url=prev_url)

@app.route('/search')
@login_required
def search():
    if not g.search_form.validate():
        return redirect(url_for('explore'))
    page = request.args.get('page', 1, type=int)
    q = g.search_form.q.data
    query = sa.select(Collection).where(
        Collection.name.ilike(f'%{q}%')
    ).order_by(Collection.timestamp.desc())
    collections = db.paginate(query, page=page,
                              per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('search', q=q, page=collections.next_num) \
        if collections.has_next else None
    prev_url = url_for('search', q=q, page=collections.prev_num) \
        if collections.has_prev else None
    return render_template('search.html', title=f'Search: {q}', q=q,
                           collections=collections.items,
                           next_url=next_url, prev_url=prev_url)