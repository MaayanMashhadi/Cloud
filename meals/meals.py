import requests
from flask import Flask, request, jsonify, json
import sys
import pymongo
from urllib.parse import unquote
import os

# initialization of Mongo client.  docker-compose is configured to that this program only starts up after Mongo is up
# and running.
mongo_port = os.environ.get('MONGO_PORT')
client = pymongo.MongoClient(f"mongodb://mongo:{mongo_port}/")
# Warning:  do not use client = pymongo.MongoClient("mongodb://localhost:27017/") as docker-compose assigns mongo a
# unique address to the container.  In the following, db is the name of the database and wordscoll: is the name of the
# collection (e.g., table) in the db where the words will be stored.
# each document (except for cur_key) in the wordscoll collection is of the form {"_id": _id, "value": word}
db = client["fooddb"]
dishescoll = db["dishes"]
mealscoll = db["meals"]
# check if this is the first time starting up; i.e., do we already have a record with _id == 0 in the collection or not.
# If it does, do nothing.  if not, initialize
if dishescoll.find_one({"_id": 0}) is None:  # first time starting up this service as no document with _id ==0 exists
    # insert a document into the database to have one "_id" index that starts at 0 and a field named "cur_key"
    dishescoll.insert_one({"_id": 0, "cur_key": 0})
    print("Inserted document containing cur_key with _id == 0 into the collection")
    sys.stdout.flush()

if mealscoll.find_one({"_id": 0}) is None:  # first time starting up this service as no document with _id ==0 exists
    # insert a document into the database to have one "_id" index that starts at 0 and a field named "cur_key"
    mealscoll.insert_one({"_id": 0, "cur_key": 0})
    print("Inserted document containing cur_key with _id == 0 into the collection")
    sys.stdout.flush()


app = Flask(__name__)


@app.route('/dishes', methods=['POST'])
# • POST will add a dish of the given name. If successful, it returns the dish ID, a
#   positive integer, and the code 201 (Resource successfully created).
# • 0 means that request content-type is not application/json. Error code 415 (Unsupported Media Type)
# • -1 means that 'name' parameter was not specified. Error code 400 (Bad request)
# • -2 means that dish of given name already exists. Error code 400
# • -3 means that api.api-ninjas.com/v1/nutrition does not recognize this dish name. Error code 400
# • -4 means that api.api-ninjas.com/v1/nutrition was not reachable or some other server error. Error code 400
def add_dish():
    X_api_key = '/1kwy9nFcvB0xqNhnCcbXA==gbviYyFRFZqDDDBC'
    content_type = request.headers.get('Content-Type')
    # • 0 means that request content-type is not application/json. Error code 415 (Unsupported Media Type)
    # check if request content-type header exist and if it is application/json
    if content_type != 'application/json':
        return jsonify(0), 415
    req_data = request.get_json()
    req_headers = request.headers
    # • -1 means that 'name' parameter was not specified. Error code 400 (Bad request)
    if 'name' not in req_data:
        return jsonify(-1), 400
    food_name = req_data['name']
    api_url = f'https://api.api-ninjas.com/v1/nutrition?query={food_name}'
    response = requests.get(api_url, headers={'X-Api-Key': X_api_key})
    if response.status_code == requests.codes.ok:
        # • -3 means that api.api-ninjas.com/v1/nutrition does not recognize this dish name. Error code 400
        if not response.json():
            return jsonify(-3), 400
        res = response.json()
        # • -2 means that dish of given name already exists. Error code 400
        cursor = dishescoll.find({'_id': {'$gte': 1}})
        sys.stdout.flush()
        if cursor is not None:
            for doc in cursor:
                if doc['name'] == food_name:
                    return jsonify(-2), 400
        cal, size, sodium, sugar = 0, 0, 0, 0
        if len(res) >= 1:
            for item in res:
                cal += item['calories']
                size += item['serving_size_g']
                sodium += item['sodium_mg']
                sugar += item['sugar_g']
        docID = {"_id": 0}  # doc containing cur_key has the value of 0 for its "_id" field
        # retrieve the doc with "_id" value = 0 and extract the "cur_key" value from it and increment its value
        cur_key = dishescoll.find_one(docID)["cur_key"] + 1
        # set the "cur_key" field of the doc that meets the docID constraint to the updated value cur_key
        result = dishescoll.update_one(docID, {"$set": {"cur_key": cur_key}})
        result = dishescoll.insert_one({'name': food_name, '_id': cur_key,
                    'cal': cal, 'size': size,
                    'sodium': sodium, 'sugar': sugar})
        print("inserted " + food_name + " into mongo with ID " + str(result.inserted_id))
        print(result)
        sys.stdout.flush()
        return jsonify(str(cur_key)), 201
    # • -4 means that api.api-ninjas.com/v1/nutrition was not reachable or some other server error. Error code 400
    else:
        return jsonify(-4), 400


@app.route('/dishes', methods=['GET'])
# • GET will return the JSON object listing all dishes, indexed by ID
def get_dishes():
    res = []
    cursor = dishescoll.find({'_id': {'$gte': 1}})
    sys.stdout.flush()
    if cursor is not None:
        for doc in cursor:
            doc['ID'] = str(doc['_id'])
            del doc['_id']
            res.append(doc)
            sys.stdout.flush()
    return jsonify(res), 200


@app.route('/dishes/<id_or_name>', methods=['GET'])
def get_dish(id_or_name):
    # • If neither the dish ID nor a dish name is specified, the GET or DELETE
    # request returns the response -1 with error code 400 (Bad request).
    if id_or_name is None:
        return jsonify(-1), 400
    if id_or_name.isdigit():
        id = int(id_or_name)
        return get_dish_by_ID(id)
    else:
        return get_dish_by_name(id_or_name)

def get_dish_by_ID(ID):
    doc = dishescoll.find_one({'_id': ID})
    if doc is not None:
        doc['ID'] = str(doc['_id'])
        del doc['_id']
        print("mongo found ", doc, " for key ", ID)
        sys.stdout.flush()
        return jsonify(doc), 200
    # • If dish name or dish ID does not exist, the GET or DELETE request
    # returns the response -5 with error code 404 (Not Found)
    print("mongo did not find ", ID, "in find method")
    sys.stdout.flush()
    return jsonify(-5), 404

def get_dish_by_name(name):
    doc = dishescoll.find_one({'name': name})
    if doc is not None:
        doc['ID'] = str(doc['_id'])
        del doc['_id']
        print("mongo found ", doc, " for name ", name)
        sys.stdout.flush()
        return jsonify(doc), 200
    # • If dish name or dish ID does not exist, the GET or DELETE request
    # returns the response -5 with error code 404 (Not Found)
    print("mongo did not find ", name, "in find method")
    sys.stdout.flush()
    return jsonify(-5), 404


@app.route('/dishes/<id_or_name>', methods=['DELETE'])
def delete_dish(id_or_name):
    # • If neither the dish ID nor a dish name is specified, the GET or DELETE
    # request returns the response -1 with error code 400 (Bad request).
    if id_or_name is None:
        return jsonify(-1), 400
    if id_or_name.isdigit():
        id = int(id_or_name)
        return delete_dish_by_ID(id)
    else:
        return delete_dish_by_name(id_or_name)

def delete_dish_by_ID(ID):
    doc = dishescoll.find_one({'_id': ID})
    if doc is not None:
        result = dishescoll.delete_one({'_id': ID})
        if result.acknowledged and result.deleted_count >= 1:  # if result was deleted
            cursor = mealscoll.find({'_id': {'$gte': 1}})
            sys.stdout.flush()
            if cursor is not None:
                for document in cursor:
                    if document['appetizer'] == ID:
                        mealscoll.update_one(document, {"$set": {"appetizer": None}})
                    if document['main'] == ID:
                        mealscoll.update_one(document, {"$set": {"main": None}})
                    if document['dessert'] == ID:
                        mealscoll.update_one(document, {"$set": {"dessert": None}})
            return jsonify(str(ID)), 200
    # • If dish name or dish ID does not exist, the GET or DELETE request
    # returns the response -5 with error code 404 (Not Found)
    return jsonify(-5), 404

def delete_dish_by_name(name):
    doc = dishescoll.find_one({'name': name})
    if doc is not None:
        result = dishescoll.delete_one({'name': name})
        if result.acknowledged and result.deleted_count >= 1:  # if result was deleted
            cursor = mealscoll.find({'_id': {'$gte': 1}})
            sys.stdout.flush()
            if cursor is not None:
                for document in cursor:
                    if document['appetizer'] == doc['_id']:
                        mealscoll.update_one(document, {"$set": {"appetizer": None}})
                    if document['main'] == doc['_id']:
                        mealscoll.update_one(document, {"$set": {"main": None}})
                    if document['dessert'] == doc['_id']:
                        mealscoll.update_one(document, {"$set": {"dessert": None}})
            return jsonify(str(doc['_id'])), 200
    # • If dish name or dish ID does not exist, the GET or DELETE request
    # returns the response -5 with error code 404 (Not Found)
    return jsonify(-5), 404


@app.route('/meals', methods=['POST'])
# • POST will send a JSON request object with the meal name and dish IDs (appetizer,
# main, dessert). It will add that meal and return JSON meal object (consisting of
# the meal name, meal ID, appetizer ID, main ID, dessert ID, and the total calories,
# sodium and sugar content of the meal. If successful it will return a response
# code 201.
# • POST may also return a non-positive ID with the following meaning:
# • 0 means that request content-type is not application/json. Error code 415 (Unsupported Media Type)
# • -1 means that one of the required parameters was not specified correctly. Error code 400 (Bad request)
# • -5 means that one of the sent dish IDs (appetizer, main, dessert) does not exist. Error code 400
def add_meal():
    content_type = request.headers.get('Content-Type')
    # • 0 means that request content-type is not application/json. Error code 415 (Unsupported Media Type)
    # check if request content-type header exist and if it is application/json
    if content_type != 'application/json':
        return jsonify(0), 415
    req_data = request.get_json()
    req_headers = request.headers
    # • -1 means that 'name' parameter was not specified. Error code 400 (Bad request)
    if 'name' not in req_data or 'appetizer' not in req_data or 'main' not in req_data or 'dessert' not in req_data:
        return jsonify(-1), 400
    appetizer_id = int(req_data['appetizer'])
    main_id = int(req_data['main'])
    dessert_id = int(req_data['dessert'])
    # • -5 means that one of the sent dish IDs (appetizer, main, dessert) does not exist. Error code 400
    doc_appetizer = dishescoll.find_one({'_id': appetizer_id})
    doc_main = dishescoll.find_one({'_id': main_id})
    doc_desert = dishescoll.find_one({'_id': dessert_id})
    if doc_appetizer is None or doc_main is None or doc_desert is None:
        return jsonify(-5), 400

    meal_name = req_data['name']
    docID = {"_id": 0}  # doc containing cur_key has the value of 0 for its "_id" field
    # retrieve the doc with "_id" value = 0 and extract the "cur_key" value from it and increment its value
    cur_key = mealscoll.find_one(docID)["cur_key"] + 1
    # set the "cur_key" field of the doc that meets the docID constraint to the updated value cur_key
    result = mealscoll.update_one(docID, {"$set": {"cur_key": cur_key}})
    result = mealscoll.insert_one({'name': meal_name, '_id': cur_key,
                'appetizer': doc_appetizer['_id'], 'main': doc_main['_id'], 'dessert': doc_desert['_id'],
                'cal': doc_appetizer['cal'] + doc_main['cal'] + doc_desert['cal'],
                'sodium': doc_appetizer['sodium'] + doc_main['sodium'] + doc_desert['sodium'],
                'sugar': doc_appetizer['sugar'] + doc_main['sugar'] + doc_desert['sugar']})
    print("inserted " + meal_name + " into mongo with ID " + str(result.inserted_id))
    print(result)
    sys.stdout.flush()
    return jsonify(str(cur_key)), 201


@app.route('/meals', methods=['GET'])
# • GET will return the JSON object listing all dishes, indexed by ID
def get_meals():
    req_params = request.args
    if 'diet' in req_params:
        return get_meals_by_diet(req_params['diet'])
    else:
        return get_all_meals()

def get_meals_by_diet(diet):
    diet = unquote(diet)
    # send a GET request to the diet service to get the diet details
    print("diet is " + diet)
    diet_port = os.environ.get('DIETS_INTERNAL_PORT')
    diet_url = f"http://diets-service:{diet_port}/diets/" + diet
    diet_response = requests.get(diet_url)
    if diet_response.status_code == requests.codes.ok:
        if not diet_response.json():
            return jsonify(-3), 400
        res = diet_response.json()
        # get the diet details from the response
        diet_cal = res['cal']
        diet_sodium = res['sodium']
        diet_sugar = res['sugar']
        # get all meals from the meals collection
        cursor = mealscoll.find({'_id': {'$gte': 1}})
        sys.stdout.flush()
        res = []
        if cursor is not None:
            for doc in cursor:
                if doc['cal'] <= diet_cal and doc['sodium'] <= diet_sodium and doc['sugar'] <= diet_sugar:
                    doc['ID'] = str(doc['_id'])
                    del doc['_id']
                    if doc['appetizer'] is not None:
                        doc.update({'appetizer': str(doc['appetizer'])})
                    if doc['main'] is not None:
                        doc.update({'main': str(doc['main'])})
                    if doc['dessert'] is not None:
                        doc.update({'dessert': str(doc['dessert'])})
                    res.append(doc)
                    sys.stdout.flush()
        return jsonify(res), 200


def get_all_meals():
    res = []
    cursor = mealscoll.find({'_id': {'$gte': 1}})
    sys.stdout.flush()
    if cursor is not None:
        for doc in cursor:
            doc['ID'] = str(doc['_id'])
            del doc['_id']
            if doc['appetizer'] is not None:
                doc.update({'appetizer': str(doc['appetizer'])})
            if doc['main'] is not None:
                doc.update({'main': str(doc['main'])})
            if doc['dessert'] is not None:
                doc.update({'dessert': str(doc['dessert'])})
            res.append(doc)
            sys.stdout.flush()
    return jsonify(res), 200


@app.route('/meals/<id_or_name>', methods=['GET'])
def get_meal(id_or_name):
    # • If neither the meal ID nor a meal name is specified, the GET or DELETE
    # request returns the response -1 with error code 400 (Bad request).
    if id_or_name is None:
        return jsonify(-1), 400
    if id_or_name.isdigit():
        id = int(id_or_name)
        return get_meal_by_ID(id)
    else:
        return get_meal_by_name(id_or_name)

def get_meal_by_ID(ID):
    doc = mealscoll.find_one({'_id': ID})
    if doc is not None:
        doc['ID'] = str(doc['_id'])
        del doc['_id']
        if doc['appetizer'] is not None:
            doc.update({'appetizer': str(doc['appetizer'])})
        if doc['main'] is not None:
            doc.update({'main': str(doc['main'])})
        if doc['dessert'] is not None:
            doc.update({'dessert': str(doc['dessert'])})
        print("mongo found ", doc, " for key ", ID)
        sys.stdout.flush()
        return jsonify(doc), 200
    # • If meal name or meal ID does not exist, the GET or DELETE request
    # returns the response -5 with error code 404 (Not Found)
    print("mongo did not find ", ID, "in find method")
    sys.stdout.flush()
    return jsonify(-5), 404

def get_meal_by_name(name):
    doc = mealscoll.find_one({'name': name})
    if doc is not None:
        doc['ID'] = str(doc['_id'])
        del doc['_id']
        if doc['appetizer'] is not None:
            doc.update({'appetizer': str(doc['appetizer'])})
        if doc['main'] is not None:
            doc.update({'main': str(doc['main'])})
        if doc['dessert'] is not None:
            doc.update({'dessert': str(doc['dessert'])})
        print("mongo found ", doc, " for name ", name)
        sys.stdout.flush()
        return jsonify(doc), 200
    # • If meal name or meal ID does not exist, the GET or DELETE request
    # returns the response -5 with error code 404 (Not Found)
    return jsonify(-5), 404

@app.route('/meals/<id_or_name>', methods=['DELETE'])
def delete_meal(id_or_name):
    # • If neither the meal ID nor a meal name is specified, the GET or DELETE
    # request returns the response -1 with error code 400 (Bad request).
    if id_or_name is None:
        return jsonify(-1), 400
    if id_or_name.isdigit():
        id = int(id_or_name)
        return delete_meal_by_ID(id)
    else:
        return delete_meal_by_name(id_or_name)

def delete_meal_by_ID(ID):
    doc = mealscoll.find_one({'_id': ID})
    if doc is not None:
        result = mealscoll.delete_one({'_id': ID})
        if result.acknowledged and result.deleted_count >= 1:  # if result was deleted
            return jsonify(str(ID)), 200
    # • If meal name or meal ID does not exist, the GET or DELETE request
    # returns the response -5 with error code 404 (Not Found)
    return jsonify(-5), 404

def delete_meal_by_name(name):
    doc = mealscoll.find_one({'name': name})
    if doc is not None:
        result = mealscoll.delete_one({'name': name})
        if result.acknowledged and result.deleted_count >= 1:  # if result was deleted
            return jsonify(str(doc['_id'])), 200
    # • If meal name or meal ID does not exist, the GET or DELETE request
    # returns the response -5 with error code 404 (Not Found)
    return jsonify(-5), 404


@app.route('/meals/<id>', methods=['PUT'])
# • POST will send a JSON request object with the meal name and dish IDs (appetizer,
# main, dessert). It will add that meal and return JSON meal object (consisting of
# the meal name, meal ID, appetizer ID, main ID, dessert ID, and the total calories,
# sodium and sugar content of the meal. If successful it will return a response
# code 201.
# • POST may also return a non-positive ID with the following meaning:
# • 0 means that request content-type is not application/json. Error code 415 (Unsupported Media Type)
# • -1 means that one of the required parameters was not specified correctly. Error code 400 (Bad request)
# • -5 means that one of the sent dish IDs (appetizer, main, dessert) does not exist. Error code 400
def add_meal_by_id(id):
    content_type = request.headers.get('Content-Type')
    # • 0 means that request content-type is not application/json. Error code 415 (Unsupported Media Type)
    # check if request content-type header exist and if it is application/json
    if content_type != 'application/json':
        return jsonify(0), 415
    req_data = request.get_json()
    req_headers = request.headers
    # • -1 means that 'name' parameter was not specified. Error code 400 (Bad request)
    if 'name' not in req_data or 'appetizer' not in req_data or 'main' not in req_data or 'dessert' not in req_data:
        return jsonify(-1), 400
    appetizer_id = int(req_data['appetizer'])
    main_id = int(req_data['main'])
    dessert_id = int(req_data['dessert'])
    # • -5 means that one of the sent dish IDs (appetizer, main, dessert) does not exist. Error code 400
    doc_appetizer = dishescoll.find_one({'_id': appetizer_id})
    doc_main = dishescoll.find_one({'_id': main_id})
    doc_desert = dishescoll.find_one({'_id': dessert_id})
    if doc_appetizer is None or doc_main is None or doc_desert is None:
        return jsonify(-5), 400

    meal_name = req_data['name']

    docID = {"_id": 0}  # doc containing cur_key has the value of 0 for its "_id" field
    # retrieve the doc with "_id" value = 0 and extract the "cur_key" value from it and increment its value
    cur_key = mealscoll.find_one(docID)["cur_key"]
    if cur_key <= int(id):
        cur_key = int(id)
    doc = mealscoll.find_one({'_id': int(id)})
    if doc is not None:
        result = mealscoll.delete_one({'_id': int(id)})
    # set the "cur_key" field of the doc that meets the docID constraint to the updated value cur_key
    result = mealscoll.update_one(docID, {"$set": {"cur_key": cur_key}})
    result = mealscoll.insert_one({'name': meal_name, '_id': int(id),
                'appetizer': doc_appetizer['_id'], 'main': doc_main['_id'], 'dessert': doc_desert['_id'],
                'cal': doc_appetizer['cal'] + doc_main['cal'] + doc_desert['cal'],
                'sodium': doc_appetizer['sodium'] + doc_main['sodium'] + doc_desert['sodium'],
                'sugar': doc_appetizer['sugar'] + doc_main['sugar'] + doc_desert['sugar']})
    return jsonify(str(id)), 200


def main():
    app.run(host='0.0.0.0', port=80, debug=True)


if __name__ == "__main__":
    #main()
    pass
