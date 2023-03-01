from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
import random

app = Flask(__name__)

##Connect to Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


##Cafe TABLE Configuration
class Cafe(db.Model):
    id = db.Column(db.Integer, primary_key=True,autoincrement=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    location = db.Column(db.String(250), nullable=False)
    seats = db.Column(db.String(250), nullable=False)
    has_toilet = db.Column(db.Boolean, nullable=False)
    has_wifi = db.Column(db.Boolean, nullable=False)
    has_sockets = db.Column(db.Boolean, nullable=False)
    can_take_calls = db.Column(db.Boolean, nullable=False)
    coffee_price = db.Column(db.String(250), nullable=True)


@app.route("/")
def home():
    return render_template("index.html")
    

## HTTP GET - Read Record

@app.route('/random')
def get_random_cafe():
    cafes = db.session.query(Cafe).all()
    random_cafe = random.choice(cafes)
    json_cafe = {item: getattr(random_cafe, item) for item in Cafe.__table__.columns.keys()}
    return jsonify(cafe=json_cafe)



@app.route('/all')
def all():
    cafes = []
    all_cafes = Cafe.query.all()
    for cafe in all_cafes:
        del cafe.__dict__["_sa_instance_state"]
        cafes.append(cafe.__dict__)
    return jsonify(cafes=cafes)

@app.route('/search')
def search():
    loc = request.args.get("loc")
    cafes = []
    all_cafes = Cafe.query.all()

    for cafe in all_cafes:
        if cafe.__dict__["location"] == loc.capitalize():
            del cafe.__dict__["_sa_instance_state"]
            cafes.append(cafe.__dict__)

    return jsonify(cafes=cafes)

## HTTP POST - Create Record

@app.route("/create", methods=["GET", "POST"])
def rate_movie():
    names = request.args.get("name")
    map_url = request.args.get("map")
    img_url = request.args.get("image")
    loc = request.args.get("location")
    seats = request.args.get("seats")
    has_toilets = request.args.get("has_toilets")
    has_wifi = request.args.get("has_wifi")
    has_sockets = request.args.get("has_sockets")
    can_take_calls = request.args.get("calls")
    coffe_price = request.args.get("coffe_price")

    if request.method == 'POST':
        new_cafe = Cafe(
            name=names,
            map_url=map_url,
            img_url=img_url,
            location=loc,
            seats=seats,
            has_toilets=has_toilets,
            has_wifi=has_wifi,
            has_sockets=has_sockets,
            can_take_calls=can_take_calls,
            coffee_price=coffe_price
        )
        with app.app_context():
            db.session.add(new_cafe)
            db.session.commit()

    return jsonify(response={"success": "Successfully added the new cafe."})


## HTTP PUT/PATCH - Update Record

@app.route("/update/<int:cafe_id>",methods=["PATCH"])
def update(cafe_id):
    cafe = db.session.query(Cafe).get(cafe_id)
    new_price = request.args.get('new_price')
    if cafe:
        with app.app_context():
            cafe.coffee_price = new_price
            db.session.commit()
        return jsonify(response={"success": "Successfully updated the price."})
    else:
        return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."})

## HTTP DELETE - Delete Record

@app.route("/delete/<int:cafe_id>", methods=["DEL"])
def delete(cafe_id):
    cafe = db.session.query(Cafe).get(cafe_id)
    api_key = request.args.get('api_key')

    if cafe:
        if api_key == "TOPLEVELPASSCODE":
            with app.app_context():
                db.session.delete(cafe)
                db.session.commit()
            return jsonify(error={"Success": "The cafe was deleted."})

        else:
            return jsonify(error={"Authorizaton error": "Sorry that is the wrong api-key."})

    else :
        return jsonify(error={"Not Found": "Sorry a cafe with that id was not found in the database."})


if __name__ == '__main__':
    app.run(debug=True)
