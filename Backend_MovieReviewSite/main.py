# Imports
from flask import Flask, jsonify, request, make_response
from pymongo import MongoClient
import requests
import datetime
import bcrypt
import jwt
from functools import wraps
from flask_cors import CORS  # pip install flask_cors
from bson import ObjectId
# from bson.json_util import dumps
import json


# Movie Database API Setup
MOVIE_DB_API_KEY = "3d81c31b99ce2cc7902c3e1fc8fdb56c"
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_INFO_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"


# Setting up flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret-key-goes-here'


# enable Cross-Origin Resource Sharing
CORS(app)


# Setting up Pymongo database
client = MongoClient() # ('localhost', 27017)
db = client["movie&showDB"]
movie_collection = db['movies']
user_collection = db['users']
blacklist_collection = db['blacklist']


# Exporting the collections into json files
# cursor = movie_collection.find({})
# with open('movies.json', 'w') as file:
#     json.dump(json.loads(dumps(cursor)), file)


# Checks for the presence of a token
# Checks token, only if token is valid does it execute the function the wrapper is attached to
def jwt_required(func):
    @wraps(func)
    def jwt_required_wrapper(*args, **kwargs):
        token = None
        # More secure to pass it as part of the request header
        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'])
        except:
            return jsonify({'message': 'Token is invalid'}), 401

        # Make sure that the token presented is not one that is contained in the blacklist
        bl_token = blacklist_collection.find_one({"token": token})
        if bl_token is not None:
            return make_response(jsonify({'message': 'Token has been cancelled'}), 401)

        return func(*args, **kwargs)
    return jwt_required_wrapper


def admin_required(func):
    @wraps(func)
    def admin_required_wrapper(*args, **kwargs):
        token = request.headers['x-access-token']
        data = jwt.decode(token, app.config['SECRET_KEY'])
        if data["admin"]:
            return func(*args, **kwargs)
        else:
            return make_response(jsonify({'message': 'Admin access required'}), 401)
    return admin_required_wrapper


# Text Search
@app.route('/api/v1.0/movies/search', methods=["GET"])
def text_search():
    searchTerm = request.form["title"]
    movie_collection.create_index({"movieTitle": "text"}) # Setting up index
    query = {'$text': {'$search': searchTerm}} # Returns movies with the search term present in their title
    data_to_return = []
    for movie in movie_collection.find(query):
        movie["_id"] = str(movie["_id"])
        for review in movie["reviews"]:
            review["_id"] = str(review["_id"])
        data_to_return.append(movie)
    return make_response(jsonify(data_to_return), 200)


# Return only movies with reviews
@app.route('/api/v1.0/movies/reviewed', methods=["GET"])
def reviewed_movies():
    query = {"reviews": {"$gt": []}} # Returns movies that have been reviewed
    data_to_return = []
    for movie in movie_collection.find(query):
        movie["_id"] = str(movie["_id"])
        for review in movie["reviews"]:
            review["_id"] = str(review["_id"])
        data_to_return.append(movie)
    return make_response(jsonify(data_to_return), 200)


# default route, Show all items
@app.route('/api/v1.0/movies', methods=["GET"])
def get_all_items():
    # Setting up pagination
    page_num, page_size = 1, 8
    if request.args.get('pn'):
        page_num = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))
    page_start = (page_size * (page_num - 1))
    # Obtaining movie collection
    data_to_return = []
    for movie in movie_collection.find().skip(page_start).limit(page_size):
        movie["_id"] = str(movie["_id"])
        for review in movie["reviews"]:
            review["_id"] = str(review["_id"])
        data_to_return.append(movie)
    return make_response(jsonify(data_to_return), 200)


# Show single item
@app.route("/api/v1.0/movies/<string:id>", methods=["GET"])
def show_item(id):
    # Obtaining movie collection
    movie = movie_collection.find_one({"_id": ObjectId(id)})  # Fetching from the movie collection
    if movie:
        movie["_id"] = str(movie["_id"])
        for review in movie['reviews']:
            review['_id'] = str(review['_id'])
        return make_response(jsonify([movie]), 200)
    else:
        return make_response(jsonify({"error": "Invalid item ID"}), 404)



# Adding a movie using a user inputted name, running that name through an API movie database, returning options from the API
@app.route("/api/v1.0/movies/find/", methods=["GET"])
@jwt_required
def find_movie():
    movie_title = request.form["title"]
    # Calling API and obtaining data
    response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_DB_API_KEY, "query": movie_title})
    data = response.json()["results"]
    return jsonify(data)


# Using the information returned from the API to populate the movie data and add it to the database.
@app.route("/api/v1.0/movies/API-Call", methods=["GET", "POST"])
@jwt_required
def add_movie():
    movie_api_id = request.form["movie_api_id"]
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_API_KEY, "language": "en-US"})
        data = response.json()
        new_movie = {
            "movieTitle": data["title"],
            "year": data["release_date"].split("-")[0],
            "description": data["overview"],
            "img_url": f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            "reviews": [],
        }
        movie = movie_collection.insert_one(new_movie)
        new_movie_link="http://127.0.0.1:5000/api/v1.0/movies/" + str(movie.inserted_id)
        return make_response(jsonify({"url": new_movie_link}), 201)


# Update a movie
@app.route('/api/v1.0/movies/<string:id>', methods=["PUT"])
@jwt_required
def edit_movie(id):
    new_title = request.form["title"]
    new_year = request.form["year"]
    new_description = request.form["description"]
    new_url = request.form["img_url"]

    update_values = {
        "movieTitle": new_title,
        "year": new_year,
        "description": new_description,
        "img_url": new_url,
    }

    updated_movie = movie_collection.update_one({"_id": ObjectId(id)}, {"$set": update_values})

    if updated_movie.matched_count == 1:
        updated_movie_link = "http://127.0.0.1:5000/api/v1.0/movies/" + id
        return make_response(jsonify({"url": updated_movie_link}), 200)
    else:
        return make_response(jsonify({"error": "Invalid movie ID"}), 404)


# Delete a movie
@app.route('/api/v1.0/movies/<string:id>', methods=["DELETE"])
@jwt_required
@admin_required
def delete_movie(id):
    item = movie_collection.delete_one({"_id": ObjectId(id)})  # Deleting from the hardware collection

    if item:
        return make_response(jsonify({"success": "Successfully deleted movie"}), 204)
    else:
        return jsonify({"error": "Invalid movie ID"}), 404


# Get all reviews
@app.route('/api/v1.0/movies/<string:id>/reviews/', methods=['GET'])
def get_all_reviews(id):
    data_to_return = []
    movie = movie_collection.find_one({"_id": ObjectId(id)}, {"reviews":1, "_id":0})
    if movie:
        for review in movie['reviews']:
            review['_id'] = str(review['_id'])
            data_to_return.append(review)
        return make_response(jsonify(data_to_return), 200)
    else:
        return make_response(jsonify({"error": "Invalid item ID"}), 404)


# Get one review
@app.route('/api/v1.0/movies/<mid>/reviews/<rid>', methods=['GET'])
def get_one_review(mid, rid):
    movie = movie_collection.find_one({"reviews._id": ObjectId(rid)}, {"_id": 0, "reviews.$": 1})
    if movie is None:
        return make_response(jsonify({"error": "Invalid movie ID or review ID"}), 404)
    movie["reviews"][0]["_id"] = str(movie["reviews"][0]["_id"])
    return make_response(jsonify(movie['reviews'][0]), 200)


# Adding a review
@app.route('/api/v1.0/movies/<string:id>/reviews/', methods=['POST'])
# @jwt_required
def add_review(id):
    new_review = {
        "_id": ObjectId(),
        "username": request.form["username"],
        "review": request.form["review"],
        "rating": request.form["rating"],
        "date": request.form["date"],
    }

    movie_collection.update_one({"_id": ObjectId(id)}, {"$push": {"reviews": new_review}})
    new_review_link = "http://127.0.0.1:5000/api/v1.0/movies/" + id + "/reviews/" + str(new_review["_id"])
    return make_response(jsonify({"url": new_review_link}), 201)


# Update a review
@app.route('/api/v1.0/movies/<mid>/reviews/<rid>', methods=['PUT'])
@jwt_required
def update_review(mid, rid):
    username = request.form["username"]
    review = request.form["review"]
    rating = request.form["rating"]

    update_values = {
        "reviews.$.username": username,
        "reviews.$.review": review,
        "reviews.$.rating": rating,
    }

    updated_review = movie_collection.update_one({"reviews._id": ObjectId(rid)}, {"$set": update_values})
    if updated_review.matched_count == 1:
        updated_review_link = "http://127.0.0.1:5000/api/v1.0/movies/" + mid + "/reviews/" + rid
        return make_response(jsonify({"url": updated_review_link}), 200)
    else:
        return make_response(jsonify({"error": "Invalid review ID"}), 404)


# Delete Review
@app.route('/api/v1.0/movies/<mid>/reviews/<rid>', methods=['DELETE'])
@jwt_required
@admin_required
def delete_review(mid, rid):
    movie_collection.update_one({"_id": ObjectId(mid)}, {"$pull": {"reviews": {"_id": ObjectId(rid)}}})
    return make_response(jsonify({"success": "Successfully deleted movie"}), 204)


@app.route('/api/v1.0/register/', methods=["POST"])
def register():
    name = request.form["name"]
    username = request.form["username"]
    admin = request.form["admin"]
    email = request.form["email"]
    password = request.form["password"]
    query = {"email": email}
    result = user_collection.find_one(query)
    # Note, email in db is unique so will only have one result.
    user = result
    if user:
        # User already exists
        return jsonify({"message": "You've already signed up with that email, log in instead!"}), 404
    # Hashing and salting the password entered by the user
    hash_and_salted_password = bcrypt.hashpw((bytes(password, 'UTF-8')), bcrypt.gensalt())

    new_user = {
        "name": name,
        "username": username,
        "email": email,
        "password": hash_and_salted_password,
        "admin": admin
    }

    user_collection.insert_one(new_user)
    return make_response(jsonify({"success": "Successfully registered"}), 201)


@app.route('/api/v1.0/login/', methods=["GET"])
def login():
    auth = request.authorization
    if auth:
        user = user_collection.find_one({'username': auth.username})
        if user is not None:
            if bcrypt.checkpw(bytes(auth.password, 'UTF-8'), user["password"]):
                token = jwt.encode({'user': auth.username, 'admin': user["admin"], 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
                return make_response(jsonify({'token': token.decode('UTF-8')}), 200)
            else:
                return make_response(jsonify({'message': 'Bad password'}), 401)
        else:
            return make_response(jsonify({'message': 'Bad email'}), 401)
    return make_response(jsonify({'message': 'Authentication required'}), 401)


@app.route('/api/v1.0/logout', methods=["GET"])
@jwt_required
def logout():
    token = request.headers['x-access-token']
    blacklist_collection.insert_one({"token": token})
    return make_response(jsonify({'message': 'Logout successful'}), 200)


if __name__ == '__main__':
    app.run(debug=True)