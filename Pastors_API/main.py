from flask import Flask, render_template, request, url_for, redirect, flash
import werkzeug.security
from werkzeug.security import check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager
# from flask_wtf import FlaskForm
# from wtforms import StringField, SubmitField, SelectMultipleField, IntegerField, EmailField

app = Flask(__name__)
app.config['STATIC_FOLDER'] = 'static'

login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'any-secret-key-you-choose'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


"""CREATE TABLE IN DB"""


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))


"""incase you want to use flask forms"""
"""class LoginForm(FlaskForm):
    name = StringField("Name")
    email = EmailFieldField("Email")
    submit = SubmitField("Submit")"""

"""The below code is for if you want to add an endpoint to the home page"""

"""@app.route('/')
def home():
    return render_template("index.html")"""


@app.route('/register', methods=['GET', 'POST'])
def register():
    """form = LoginForm()"""
    if request.method == 'POST':
        password = werkzeug.security.generate_password_hash(request.form.get("password"), method='pbkdf2:sha256', salt_length=8)
        new_user = User(
            name=request.form.get("name"),
            email=request.form.get("email"),
            password=password
        )
        with app.app_context():
            db.session.add(new_user)
            db.session.commit()
            """the below line takes them to the login page after they register"""
        return render_template("login.html")

    return render_template("register.html")


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            """"input where to go after login"""
            return redirect(url_for('/'))
    return render_template("login.html", form=form)


"""


@app.route('/logout')
def logout():
    pass 
    """


"""
In the register.html file, replace this line:

<form method="get" action="{{ url_for('register') }}">
with:

<form method="post" action="{{ url_for('register') }}">



Similarly, in the login.html file, replace this line:

<form method="get" action="{{ url_for('login') }}">

with:

<form method="post" action="{{ url_for('login') }}">"""




if __name__ == "__main__":
    app.run(debug=True)
