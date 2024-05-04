from flask_sqlalchemy import SQLAlchemy
from flask import jsonify
import random

random.randint(0, 10)


generate_id = lambda: "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789") for _ in range(6))


db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(6), primary_key=True, default=generate_id)
    email = db.Column(db.String(120), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_active = db.Column(db.Boolean(), unique=False, nullable=False, default=True) 
    favorite_planets = db.relationship('Planet', secondary='user_planet_favorites', backref='favorited_by')
    favorite_characters = db.relationship('Character', secondary='user_character_favorites', backref='favorited_by')

    def __repr__(self):
        return f"User {self.name}, Id: {self.id}"
    
    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "is_active": self.is_active
        }
    def serialize_favorites(self):
        return{
        "favorite_planets": [planet.serialize() for planet in self.favorite_planets],
        "favorite_characters": [character.serialize() for character in self.favorite_characters]
        }

class Planet(db.Model):
    __tablename__ = 'planets'

    id = db.Column(db.String(6), primary_key=True, default=generate_id)
    name = db.Column(db.String, nullable=False)
    population = db.Column(db.Integer, nullable=False)
    terrain = db.Column(db.String, nullable=False)
    favorite_of = db.relationship('User', secondary='user_planet_favorites')
    
    def __repr__(self):
        return f"Planet {self.name}, Id: {self.id}"
    
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "population": self.population,
            "terrain": self.terrain
        }
    
class Character(db.Model):
    __tablename__ = 'characters'

    id = db.Column(db.String(6), primary_key=True, default=generate_id)
    name = db.Column(db.String, nullable=False)
    hair_color = db.Column(db.String, nullable=False)
    eye_color = db.Column(db.String, nullable=False)
    gender = db.Column(db.String, nullable=False)
    favorite_of = db.relationship('User', secondary='user_character_favorites')

    def __repr__(self):
        return f"Character {self.name}, Id: {self.id}"
    
    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "hair_color": self.hair_color,
            "eye_color": self.eye_color,
            "gender": self.gender
        }

class UserPlanetFavorite(db.Model):
    __tablename__ = 'user_planet_favorites'

    user_id = db.Column(db.String, db.ForeignKey('users.id'), primary_key=True)
    planet_id = db.Column(db.String, db.ForeignKey('planets.id'), primary_key=True)

    user = db.relationship('User', backref=db.backref('planet_favorites', cascade='all, delete-orphan'))
    planet = db.relationship('Planet', backref=db.backref('user_favorites', cascade='all, delete-orphan'))


    def serialize(self):
        return{
        "User:": [user.serialize() for user in self.user_id],
        "Planet in favorites:": [planet.serialize() for planet in self.planet_id],

        "User": self.user.name,
        "Planet in favorites": self.planet.name
        }

class UserCharacterFavorite(db.Model):
    __tablename__ = 'user_character_favorites'

    user_id = db.Column(db.String, db.ForeignKey('users.id'), primary_key=True)
    character_id = db.Column(db.String, db.ForeignKey('characters.id'), primary_key=True)

    user = db.relationship('User', backref=db.backref('character_favorites', cascade='all, delete-orphan'))
    character = db.relationship('Character', backref=db.backref('user_favorites', cascade='all, delete-orphan'))

    def serialize(self):
        return{
        "User:": [user.serialize() for user in self.user_id],
        "Person in favorites:": [character.serialize() for character in self.character_id],

        "User": self.user.name,
        "Character in favorites": self.character.name
        }

# methods:

def add(model_type, data):
    noobie = model_type(**data)
    try:
        db.session.add(noobie)
        db.session.commit()
        return jsonify(f"{model_type.__name__} added successfully."), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(f"Error adding {model_type.__name__}: {str(e)}."), 400

def delete(model_type, data):
    doomed = db.session.query(model_type).filter_by(**data).first()
    if not doomed:
        return jsonify(f"{model_type.__name__} not found."), 404
    try:
        db.session.delete(doomed)
        db.session.commit()
        return jsonify(f"{model_type.__name__} deleted successfully."), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(f"Error deleting {model_type.__name__}: {str(e)}."), 400


def update(model_type, data):
    oopsie = db.session.query(model_type).filter_by(id = data["id"]).first()
    if not oopsie:
        return jsonify(f"{data.get('name')} not found in {model_type.__name__}."), 404
    try:
        for key, value in data.items():
            setattr(oopsie, key, value)
        db.session.commit()
        return jsonify(f"{model_type.__name__} updated successfully."), 201
    except Exception as e:
        db.session.rollback()
        return jsonify(f"Error updating {model_type.__name__}: {str(e)}."), 400

def get(model_type, data):
    if "id" in data:
        individual = db.query(model_type).filter_by(id = data["id"]).first
        if not individual:
            return jsonify(f"{model_type} {data['id']} not found."), 404
        return jsonify(individual.serialize())
    society = db.session.query(model_type).all()
    if not society:
        return jsonify(f"Table {model_type.__name__} not found."), 404
    print("we're about to return")
    return jsonify([item.serialize() for item in society])

meth = {
    "add": add,
    "delete": delete,
    "update": update,
    "get": get
}