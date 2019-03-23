import datetime
import os
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from data import Articles
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime
from passlib.hash import sha256_crypt
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from functools import wraps

app = Flask(__name__)
db_path = os.path.join(os.path.dirname(__file__), 'hgdatabase.db')
db_uri = 'sqlite:///{}'.format(db_path)
app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
db = SQLAlchemy(app)

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(90))
    username = db.Column(db.String(30))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))
    register_date = db.Column(DateTime, default=datetime.datetime.utcnow)


class Articles(db.Model):
    __tablename__ = 'articles'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    user = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = db.Column(db.String(100))
    body = db.Column(db.String())
    created_date = db.Column(DateTime, default=datetime.datetime.utcnow)

db.create_all()
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    get_all = Articles.query.all()
    if get_all:
        return render_template('articles.html', articles=get_all)
    else:
        msg = 'No articles found'
        return render_template('articles.html', msg=msg)


@app.route('/article/<string:id>/')
def article(id):
    get_article = Articles.query.filter_by(id=id).first()
    return render_template('article.html', article=get_article)

def logged_wrapper(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, log in', 'danger')
            return redirect(url_for('login'))
    return wrap

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=40)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')])
    confirm = PasswordField('Confirm Password')

class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])


@app.route('/register', methods=['GET' ,'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))
        user = Users(name=name, email=email, username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now part of hellgate')
        return redirect(url_for('index'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password_candidate = request.form['password']
        user = Users.query.filter_by(username=username).first()
        if user:
            password = user.password
            identification = user.id
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                session['id'] = identification
                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = "Invalid password"
                return render_template('login.html', error=error)
        else:
            error = "Invalid username"
            return render_template('login.html', error=error)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@logged_wrapper
def dashboard():
    flash(Articles.query.filter_by(user=Users.id).all())
    flash(session["id"])
    get_all = Articles.query.filter_by(user=session["id"])
    if get_all:
        return render_template('dashboard.html', articles=get_all)
    else:
        msg = 'No articles found'
        return render_template('dashboard.html', msg=msg)

@app.route('/add_article', methods =['GET', 'POST'])
@logged_wrapper
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data
        article = Articles(title=title, body=body, author=session['username'])
        db.session.add(article)
        db.session.commit()
        db.session.close()
        flash('Succesfully added article', 'success')
        return redirect(url_for('dashboard'))
    return render_template('add_article.html', form=form)

@app.route('/edit_article/<string:id>', methods=["GET", "POST"])
@logged_wrapper
def edit_article(id):
    art = Articles.query.filter_by(id=id).one()
    form = ArticleForm(request.form)
    form.title.data = art.title
    form.body.data = art.body
    if request.method == "POST" and form.validate():
        title = request.form['title']
        body = request.form['body']
        art.body = body
        art.title = title
        db.session.commit()
        db.session.close()
        return redirect(url_for('dashboard'))
    return render_template('edit_article.html', form=form)

@app.route('/delete_article/<string:id>', methods=['POST'])
@logged_wrapper
def delete_article(id):
    art = Articles.query.filter_by(id=id).one()
    db.session.delete(art)
    db.session.commit()
    flash('deleted', 'success')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key=os.environ["hg_secret_flask"]
    app.run(debug=True, host='0.0.0.0', port=1400)
