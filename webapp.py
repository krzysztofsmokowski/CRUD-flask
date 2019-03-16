import datetime
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from data import Articles
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime
from passlib.hash import sha256_crypt
from wtforms import Form, StringField, TextAreaField, PasswordField, validators


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hgdatabase.db'
db = SQLAlchemy(app)

class Users(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(90))
    username = db.Column(db.String(30))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))
    register_date = db.Column(DateTime, default=datetime.datetime.utcnow)

db.create_all()
Articles = Articles()
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    return render_template('articles.html', articles=Articles)

@app.route('/article/<string:id>/')
def article(id):
    return render_template('article.html', id=id)

class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=40)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')])
    confirm = PasswordField('Confirm Password')

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

if __name__ == '__main__':
    app.secret_key='topsecrethellgate'
    app.run(debug=True, host='0.0.0.0', port=80)
