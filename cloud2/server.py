import requests
from flask import Flask, request, jsonify, json

dish = []
meal = []
dish_counter = 0
meal_counter = 0

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
    global dish_counter, dish
    X_api_key = '/1kwy9nFcvB0xqNhnCcbXA==gbviYyFRFZqDDDBC'
    req_data = request.get_json()
    req_headers = request.headers
    # • 0 means that request content-type is not application/json. Error code 415 (Unsupported Media Type)
    # check if request content-type header exist and if it is application/json
    if 'Content-Type' not in req_headers or req_headers['Content-Type'] != 'application/json':
        return jsonify(0), 415
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
        for item in dish:
            if food_name == item['name']:
                return jsonify(-2), 400
        cal, size, sodium, sugar = 0, 0, 0, 0
        if len(res) >= 1:
            for item in res:
                cal += item['calories']
                size += item['serving_size_g']
                sodium += item['sodium_mg']
                sugar += item['sugar_g']
        dish_counter += 1
        dish.append({'name': food_name, 'ID': str(dish_counter),
                    'cal': cal, 'size': size,
                    'sodium': sodium, 'sugar': sugar})
        return jsonify(str(dish_counter)), 201
    # • -4 means that api.api-ninjas.com/v1/nutrition was not reachable or some other server error. Error code 400
    else:
        return jsonify(-4), 400


@app.route('/dishes', methods=['GET'])
# • GET will return the JSON object listing all dishes, indexed by ID
def get_dishes():
    global dish
    res = {}
    for item in dish:
        res[item['ID']] = item
    return jsonify(res), 200


@app.route('/dishes/<id_or_name>', methods=['GET'])
def get_dish(id_or_name):
    # • If neither the dish ID nor a dish name is specified, the GET or DELETE
    # request returns the response -1 with error code 400 (Bad request).
    if id_or_name is None:
        return jsonify(-1), 400
    if id_or_name.isdigit():
        id = str(id_or_name)
        return get_dish_by_ID(id)
    else:
        return get_dish_by_name(id_or_name)

def get_dish_by_ID(ID):
    global dish
    for item in dish:
        if item['ID'] == str(ID):
            return jsonify(item), 200
    # • If dish name or dish ID does not exist, the GET or DELETE request
    # returns the response -5 with error code 404 (Not Found)
    return jsonify(-5), 404

def get_dish_by_name(name):
    global dish
    for item in dish:
        if item['name'] == name:
            return jsonify(item), 200
    # • If dish name or dish ID does not exist, the GET or DELETE request
    # returns the response -5 with error code 404 (Not Found)
    return jsonify(-5), 404


@app.route('/dishes/<id_or_name>', methods=['DELETE'])
def delete_dish(id_or_name):
    # • If neither the dish ID nor a dish name is specified, the GET or DELETE
    # request returns the response -1 with error code 400 (Bad request).
    if id_or_name is None:
        return jsonify(-1), 400
    if id_or_name.isdigit():
        id = str(id_or_name)
        return delete_dish_by_ID(id)
    else:
        return delete_dish_by_name(id_or_name)

def delete_dish_by_ID(ID):
    global dish
    for item in dish:
        if item['ID'] == str(ID):
            dish.remove(item)
            for item in meal:
                if item['appetizer'] == str(ID):
                    item['appetizer'] = None
                if item['main'] == str(ID):
                    item['main'] = None
                if item['dessert'] == str(ID):
                    item['dessert'] = None
            return jsonify(str(ID)), 200
    # • If dish name or dish ID does not exist, the GET or DELETE request
    # returns the response -5 with error code 404 (Not Found)
    return jsonify(-5), 404

def delete_dish_by_name(name):
    global dish
    for item in dish:
        if item['name'] == name:
            dish.remove(item)
            id = item['ID']
            for item in meal:
                if item['appetizer'] == id:
                    item['appetizer'] = None
                if item['main'] == id:
                    item['main'] = None
                if item['dessert'] == id:
                    item['dessert'] = None
            return jsonify(item['ID']), 200
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
# • -2 means that a meal of the given name already exists. Error code 400
# • -5 means that one of the sent dish IDs (appetizer, main, dessert) does not exist. Error code 400
def add_meal():
    global meal_counter, dish, meal
    req_data = request.get_json()
    req_headers = request.headers
    # • 0 means that request content-type is not application/json. Error code 415 (Unsupported Media Type)
    # check if request content-type header exist and if it is application/json
    if 'Content-Type' not in req_headers or req_headers['Content-Type'] != 'application/json':
        return jsonify(0), 415
    # • -1 means that 'name' parameter was not specified. Error code 400 (Bad request)
    if ('name' or 'appetizer' or 'main' or 'dessert') not in req_data:
        return jsonify(-1), 400
    appetizer_id = str(req_data['appetizer'])
    main_id = str(req_data['main'])
    dessert_id = str(req_data['dessert'])
    # • -5 means that one of the sent dish IDs (appetizer, main, dessert) does not exist. Error code 400
    find = 0
    for item in dish:
        if item['ID'] == appetizer_id:
            appetizer_dish = item
            find += 1
        if item['ID'] == main_id:
            main_dish = item
            find += 1
        if item['ID'] == dessert_id:
            dessert_dish = item
            find += 1
    if find != 3:
        return jsonify(-5), 400
    meal_name = req_data['name']
    # • -2 means that dish of given name already exists. Error code 400
    for item in meal:
        if meal_name == item['name']:
            return jsonify(-2), 400
    meal_counter += 1
    meal.append({'name': meal_name, 'ID': str(meal_counter),
                'appetizer': appetizer_dish['ID'], 'main': main_dish['ID'], 'dessert': dessert_dish['ID'],
                'cal': appetizer_dish['cal'] + main_dish['cal'] + dessert_dish['cal'],
                'sodium': appetizer_dish['sodium'] + main_dish['sodium'] + dessert_dish['sodium'],
                'sugar': appetizer_dish['sugar'] + main_dish['sugar'] + dessert_dish['sugar']})
    return jsonify(meal_counter), 201


@app.route('/meals', methods=['GET'])
# • GET will return the JSON object listing all dishes, indexed by ID
def get_meals():
    global meal
    res = {}
    for item in meal:
        res[item['ID']] = item
    return jsonify(res), 200


@app.route('/meals/<id_or_name>', methods=['GET'])
def get_meal(id_or_name):
    # • If neither the meal ID nor a meal name is specified, the GET or DELETE
    # request returns the response -1 with error code 400 (Bad request).
    if id_or_name is None:
        return jsonify(-1), 400
    if id_or_name.isdigit():
        id = str(id_or_name)
        return get_meal_by_ID(id)
    else:
        return get_meal_by_name(id_or_name)

def get_meal_by_ID(ID):
    global meal
    for item in meal:
        if item['ID'] == str(ID):
            return jsonify(item), 200
    # • If meal name or meal ID does not exist, the GET or DELETE request
    # returns the response -5 with error code 404 (Not Found)
    return jsonify(-5), 404

def get_meal_by_name(name):
    global meal
    for item in meal:
        if item['name'] == name:
            return jsonify(item), 200
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
        id = str(id_or_name)
        return delete_meal_by_ID(id)
    else:
        return delete_meal_by_name(id_or_name)

def delete_meal_by_ID(ID):
    global meal
    for item in meal:
        if item['ID'] == str(ID):
            meal.remove(item)
            return jsonify(ID), 200
    # • If meal name or meal ID does not exist, the GET or DELETE request
    # returns the response -5 with error code 404 (Not Found)
    return jsonify(-5), 404

def delete_meal_by_name(name):
    global meal
    for item in meal:
        if item['name'] == name:
            meal.remove(item)
            return jsonify(item['ID']), 200
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
    global meal_counter, dish, meal
    req_data = request.get_json()
    req_headers = request.headers
    # • 0 means that request content-type is not application/json. Error code 415 (Unsupported Media Type)
    # check if request content-type header exist and if it is application/json
    if 'Content-Type' not in req_headers or req_headers['Content-Type'] != 'application/json':
        return jsonify(0), 415
    # • -1 means that 'name' parameter was not specified. Error code 400 (Bad request)
    if ('name' or 'appetizer' or 'main' or 'dessert') not in req_data:
        return jsonify(-1), 400
    appetizer_id = str(req_data['appetizer'])
    main_id = str(req_data['main'])
    dessert_id = str(req_data['dessert'])
    # • -5 means that one of the sent dish IDs (appetizer, main, dessert) does not exist. Error code 400
    find = 0
    for item in dish:
        if item['ID'] == appetizer_id:
            appetizer_dish = item
            find += 1
        if item['ID'] == main_id:
            main_dish = item
            find += 1
        if item['ID'] == dessert_id:
            dessert_dish = item
            find += 1
    if find != 3:
        return jsonify(-5), 400

    meal_name = req_data['name']
    meal_counter += 1
    meal.append({'name': meal_name, 'ID': str(id),
                'appetizer': appetizer_dish['ID'], 'main': main_dish['ID'], 'dessert': dessert_dish['ID'],
                'cal': appetizer_dish['cal'] + main_dish['cal'] + dessert_dish['cal'],
                'sodium': appetizer_dish['sodium'] + main_dish['sodium'] + dessert_dish['sodium'],
                'sugar': appetizer_dish['sugar'] + main_dish['sugar'] + dessert_dish['sugar']})
    return jsonify(str(id)), 200


def main():
    app.run(host='0.0.0.0', port=80, debug=True)


if __name__ == "__main__":
    #main()
    pass
