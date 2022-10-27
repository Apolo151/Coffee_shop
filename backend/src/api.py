import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

# ROUTES

'''
GET /drinks
        it is a public endpoint
        it only contains the drink.short() data representation

    returns status code 200 and json {"success": True, "drinks": drinks}
    where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''


@app.route('/drinks')
def get_drinks():
    drinks = Drink.query.all()
    drinks_short = [drink.short() for drink in drinks]
    return jsonify({
            "success": True,
            "drinks": drinks_short
        }), 200

'''
    GET /drinks-detail
        it requires the 'get:drinks-detail' permission
        it contains the drink.long() data representation

    returns status code 200 and json {"success": True, "drinks": drinks}
    where drinks is the list of drinks
    or appropriate status code indicating reason for failure
'''


@app.route("/drinks-detail")
@requires_auth("get:drinks_detail")
def get_drinks_detail(payload):
    drinks = Drink.query.all()
    drinks_long = [drink.long() for drink in drinks]
    return jsonify({
        "success": True,
        "drinks": drinks_long
    }), 200

'''
    POST /drinks
        it creates a new row in the drinks table
        it requires the 'post:drinks' permission
        it contains the drink.long() data representation

    returns status code 200 and json {"success": True, "drinks": drink}
    where drink an array containing only the newly created drink
    or appropriate status code indicating reason for failure
'''


@app.route("/drinks", methods=['POST'])
@requires_auth("post:drinks")
def add_drink(payload):
    try:
        drink_details = request.get_json()
        title = drink_details.get("title")
        recipe = drink_details.get("recipe")

        drink = Drink(title=title, recipe=json.dumps(recipe))
        drink.insert()
        drink_array = []
        find_drink = Drink.query.filter(Drink.title == title).one_or_none()
        if find_drink is None:
            abort(422)
        drink_array.append(find_drink.long())
        return jsonify({
            "success": True,
            "drinks": drink_array
        }), 200
    except Exception as e:
        print(e)
        abort(422)

'''
    PATCH /drinks/<id>
        where <id> is the existing model id
        it responds with a 404 error if <id> is not found
        it updates the corresponding row for <id>
        it requires the 'patch:drinks' permission
        it contains the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink}
    where drink an array containing only the updated drink
    or appropriate status code indicating reason for failure
'''


@app.route("/drinks/<id>", methods=['PATCH'])
@requires_auth("patch:drinks")
def update_drink(payload, id):
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink is None:
            abort(404)
        title = request.get_json().get("title")
        recipe = request.get_json().get("recipe")
        if recipe is not None:
            if type(recipe) == str:
                drink.recipe = recipe
            else:
                drink.recipe = json.dumps(recipe)
        if title is not None:
            drink.title = title
        drink.update()
        the_updated_drink = []
        updated_drink = Drink.query.filter(Drink.id == id).one_or_none()
        the_updated_drink.append(updated_drink.long())
        return jsonify({
            "success": True,
            "drinks": the_updated_drink
        }), 200
    except Exception as e:
        print(e)
        abort(422)

'''
    DELETE /drinks/<id>
        where <id> is the existing model id
        it responds with a 404 error if <id> is not found
        it deletes the corresponding row for <id>
        it requires the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id}
    where id is the id of the deleted record
    or appropriate status code indicating reason for failure
'''


@app.route("/drinks/<id>", methods=['DELETE'])
@requires_auth("delete:drinks")
def delete_drink(payload, id):
    try:
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink is None:
            abort(404)
        drink.delete()
        return jsonify({
            "success": True,
            "deleted": id
        }), 200
    except Exception as e:
        print(e)
        abort(422)


# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
        }), 422


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 404


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "internal server error"
    }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(AuthError)
def Auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error
    }), error.status_code
