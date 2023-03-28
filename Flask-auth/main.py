from flask import Flask, render_template, request, url_for, redirect, flash, send_from_directory
import werkzeug.security
from werkzeug.security import check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from flask_pymongo import PyMongo

app = Flask(__name__)
app.config['STATIC_FOLDER'] = 'static'

login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'any-secret-key-you-choose'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/mydatabase'
mongo = PyMongo(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


##CREATE TABLE IN DB
class User(db.Document):
    username = db.StringField(required=True)
    email = db.StringField(required=True)
    password = db.StringField(required=True)

#Line below only required once, when creating DB. 


@app.route('/')
def home():
    return render_template("index.html")



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        password = werkzeug.security.generate_password_hash(request.form['password'], method='pbkdf2:sha256', salt_length=8)
        new_user = User(
            name=request.form['name'],
            email=request.form['email'],
            password=password
        )
        with app.app_context():
            db.session.add(new_user)
            db.session.commit()
        return redirect(url_for("secrets"))

    return render_template("register.html")


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/secrets')
def secrets():
    return render_template("secrets.html")


@app.route('/logout')
def logout():
    pass


@app.route('/download')
def download_file():
    return send_from_directory('static', filename="files/cheat_sheet.pdf")


if __name__ == "__main__":
    app.run(debug=True)
