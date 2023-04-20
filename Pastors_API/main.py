from flask import Flask, request, url_for, redirect, flash
import werkzeug.security
from werkzeug.security import check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager

app = Flask(__name__)
app.config['STATIC_FOLDER'] = 'static'

login_manager = LoginManager()
login_manager.init_app(app)
app.config['SECRET_KEY'] = 'any-secret-key-you-choose'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(100), unique=False)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.get_json()
        password = werkzeug.security.generate_password_hash(data.get("password"), method='pbkdf2:sha256', salt_length=8)
        new_user = User(
            name=data.get("name"),
            email=data.get("email"),
            password=password
        )
        with app.app_context():
            db.session.add(new_user)
            db.session.commit()


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

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

        cred = {"name": user.name,
                "email": email }
        return cred



if __name__ == "__main__":
    app.run(debug=True)
