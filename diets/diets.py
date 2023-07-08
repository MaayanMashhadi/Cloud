import json
import sys

from flask import Flask, request, jsonify
from flask_restful import Api, reqparse
import pymongo
import os

app = Flask(__name__)  # initialize Flask
api = Api(app)  # create API

# initialization of Mongo client.  docker-compose is configured to that this program only starts up after Mongo is up
# and running.
mongo_port = os.environ.get('MONGO_PORT')
client = pymongo.MongoClient(f"mongodb://mongo:{mongo_port}/")
# Warning:  do not use client = pymongo.MongoClient("mongodb://localhost:27017/") as docker-compose assigns mongo a
# unique address to the container.  In the following, db is the name of the database and wordscoll: is the name of the
# collection (e.g., table) in the db where the words will be stored.
# each document (except for cur_key) in the wordscoll collection is of the form {"_id": _id, "value": word}
db = client["fooddb"]
dietscoll = db["diets"]
# check if this is the first time starting up; i.e., do we already have a record with _id == 0 in the collection or not.
# If it does, do nothing.  if not, initialize
if dietscoll.find_one({"_id": 0}) is None:  # first time starting up this service as no document with _id ==0 exists
    # insert a document into the database to have one "_id" index that starts at 0 and a field named "cur_key"
    dietscoll.insert_one({"_id": 0, "cur_key": 0})
    print("Inserted document containing cur_key with _id == 0 into the collection")
    sys.stdout.flush()


@app.route('/diets', methods=['POST'])
def post_diets():
    content_type = request.headers.get('Content-Type')
    # • If the POST request did not supply JSON content, then it returns “POST
    # expects content type to be application/json” with a status code of 415.
    if content_type != 'application/json':
        return jsonify("POST expects content type to be application/json"), 415
    req_data = request.get_json()
    req_headers = request.headers
    # • If the JSON object is ill-formed such as not containing a “cal”, “sodium” or
    # “sugar” field, then it returns “Incorrect POST format” with a status code of
    # 422.
    if 'name' not in req_data or 'cal' not in req_data or 'sodium' not in req_data or 'sugar' not in req_data:
        return jsonify("Incorrect POST format"), 422
    # • If the <name> provided for the diet is already in use (was already added), it
    # returns “Diet with <name> already exists” with a status code of 422.
    doc = dietscoll.find_one({'name': req_data['name']})
    if doc is not None:
        return jsonify(f"Diet with name {req_data['name']} already exists"), 422
    docID = {"_id": 0}  # doc containing cur_key has the value of 0 for its "_id" field
    # retrieve the doc with "_id" value = 0 and extract the "cur_key" value from it and increment its value
    cur_key = dietscoll.find_one(docID)["cur_key"] + 1
    # set the "cur_key" field of the doc that meets the docID constraint to the updated value cur_key
    result = dietscoll.update_one(docID, {"$set": {"cur_key": cur_key}})
    result = dietscoll.insert_one({"_id": cur_key, 'name': req_data['name'], 'cal': req_data['cal'],
                                    'sodium': req_data['sodium'], 'sugar': req_data['sugar']})
    sys.stdout.flush()
    # • If request is successful, it returns “Diet <name> was created successfully”
    # with a status code of 201
    return jsonify(f"Diet name {req_data['name']} was created successfully"), 201


@app.route('/diets', methods=['GET'])
def get_diets():
    res = []
    cursor = dietscoll.find({'_id': {'$gte': 1}})
    sys.stdout.flush()
    if cursor is not None:
        for doc in cursor:
            res.append({'name': doc['name'], 'cal': doc['cal'], 'sodium': doc['sodium'], 'sugar': doc['sugar']})
            sys.stdout.flush()
    return jsonify(res), 200


@app.route('/diets/<string:diet_name>', methods=['GET'])
def get_diet(diet_name):
    doc = dietscoll.find_one({'name': diet_name})
    if doc is not None:
        print("mongo found ", doc, " for name ", diet_name)
        sys.stdout.flush()
        return jsonify({'name': doc['name'], 'cal': doc['cal'], 'sodium': doc['sodium'], 'sugar': doc['sugar']}), 200
    return jsonify(f"Diet {diet_name} not found"), 404

if __name__ == "__main__":
    #main()
    pass
