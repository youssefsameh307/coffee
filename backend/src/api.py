import os
from flask import Flask, request, jsonify, abort
from flask_sqlalchemy.utils import engine_config_warning
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)




db_drop_and_create_all()


# ROUTES


@app.route('/drinks' , methods=['GET'])
def get_drinks():
    try:
        drinks = Drink.query.all()
    except:
        abort(500)
    
    shortdrinks = [x.short() for x in drinks]
    obj = {"success":True,"drinks":shortdrinks}
    return jsonify(obj)

@app.route('/error' , methods=['GET'])
def get_error():
    raise AuthError(error="error message for 403",status_code=403)


@app.route('/drinks-detail' , methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_details(payload):
    try:
        drinks = Drink.query.all()
    except:
        abort(500)
    longdrinks = [x.long() for x in drinks]
    obj = {"success":True,"drinks":longdrinks}
    return jsonify(obj)



@app.route('/drinks' , methods=['POST'])
@requires_auth('post:drinks')
def post_drink(payload):

    data = request.get_json()
    if('recipe' not in data):
        raise AuthError(error="request body doesnt have a recipe",status_code=400)
    if('title' not in data):
        raise AuthError(error="request body doesnt have a title",status_code=400)
    
    rec=str(data['recipe']).replace("'",'"')
    if rec[0]!='[':
        rec = '['+rec+']'
    insert_drink = Drink(title=data['title'],recipe=rec)


    drink = Drink.query.filter_by(title=data['title']).one_or_none()
    if drink:
        raise AuthError(error="a drink exists with this title",status_code=403)
    try:
        insert_drink.insert()
    except:
        abort(500)

    obj = {"success":True,"drinks":[insert_drink.long()]}
    return jsonify(obj)

@app.route('/drinks/<int:drink_id>' , methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drink(payload,drink_id):
    data = request.get_json()

    drink = Drink.query.filter_by(id=drink_id).one_or_none()
    if drink == None:
        raise AuthError(error="no dink exists with this id",status_code=404)


    if 'title' in data:
        drink.title = data['title']
    if 'recipe' in data:
        drink.recipe = str(data['recipe']).replace("'",'"')
    if 'recipe' not in data and 'title' not in data:
        raise AuthError(error="request body doesnt have neither a title nor a recipe",status_code=400)

    try:
        drink.update()
    except:
        abort(500)

    obj = {"success":True,"drinks":[drink.long()]}
    return jsonify(obj)


@app.route('/drinks/<int:drink_id>' , methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload,drink_id):
    try:
        drink = Drink.query.filter_by(id=drink_id).one_or_none()
    except:
        abort(500)

    if drink == None:
        raise AuthError(error="no dink exists with this id",status_code=404)


    drink.delete()

    obj = {"success":True,"drinks":drink_id}
    return jsonify(obj)

# Error Handling



@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422



@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "not found"
    }), 404

@app.errorhandler(500)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "internal server error"
    }), 500


@app.errorhandler(AuthError)
def handle_auth_error(e):
    return jsonify({
        "success": False,
        "error": e.status_code,
        "message": e.error
    }), e.status_code