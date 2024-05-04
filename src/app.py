"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, Character, UserPlanetFavorite, UserCharacterFavorite, meth

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
with app.app_context():
    db.create_all()
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/user', methods=['GET'])
def handle_hello():

    response_body = {
        "msg": "Hello, this is your GET /user response "
    }

    return jsonify(response_body), 200

#---------------------------------------------------------------------------------------------------------------------------------------∨ ∨ ∨ ∨ ∨ ∨ ∨ ∨ ∨ ∨

# need to enter user id as request body:
@app.route("/users/favorites/", methods=["GET"])
def get_favorites():
    user_id = request.get_json(force=True).get("id")
    user = db.session.query(User).filter_by(id = user_id)
    if not user: return jsonify(f"User {user_id} not found."), 404
    return jsonify(user.serialize_favorites())

# need to enter user id as request body:
@app.route("/favorite/<string:type>/<string:obj_id>/", methods=["POST", "DELETE"])
def generic_actions(type, obj_id):

    if type == "planet":
        model_type = UserPlanetFavorite
        ids = {"planet_id": obj_id}
    elif type == "people":
        model_type = UserCharacterFavorite
        ids = {"character_id": obj_id}
    else: return jsonify({"msg": "No favorites with that name found"}), 404

    data = request.get_json(force=True).get("id") or request.get_json(force=True).get("id")
    if not data: return jsonify({"Error": "No user id was provided"}), 400
    ids["user_id"] = data

    if request.method == "POST":
        return meth.add(model_type, ids)

    elif request.method == "DELETE":
        return meth.delete(model_type, ids)

@app.route("/<string:type>/", defaults={'obj_id': None}, methods=["GET", "POST", "PUT", "DELETE"], endpoint="without_id")
#@app.route("/<string:type>/<string:obj_id>/", methods=["GET", "POST", "DELETE", "PUT"], endpoint="with_id")
def generic_actions(type, obj_id):

    model_mapping = {
        "users": User,
        "planets": Planet,
        "people": Character,
        "favorite_planets": UserPlanetFavorite,
        "favorite_people": UserCharacterFavorite
    }
    model_type = model_mapping.get(type)
    if not model_type: return jsonify({"msg": "No table with that name found"}), 404

    data = request.get_json(force=True) or {}
    if obj_id: data["id"] = obj_id

    if request.method == "GET":
        return meth.get(model_type, data)

    elif request.method == "POST":
        return meth.add(model_type, data)

    elif request.method == "DELETE":
        return meth.delete(model_type, data)

    elif request.method == "PUT":
        return meth.update(model_type, data)



#---------------------------------------------------------------------------------------------------------------------------------------∧ ∧ ∧ ∧ ∧ ∧ ∧ ∧ ∧ ∧

@app.route('/users')
def list_users():
    users = db.session.query(User).all()
    return jsonify([user.serialize() for user in users])


# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=True)
