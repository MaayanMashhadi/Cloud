import requests
import json

orange = 'orange'
spaghetti = 'spaghetti'
apple_pie = 'apple pie'

delicious = 'delicious'

meals_resource = '/meals'
dishes_resource = '/dishes'

import pytest
import server
import requests

global dishes, dishes_id, meal_id
dishes = ["orange", "spaghetti", "apple pie"]
dishes_id = [""] * len(dishes)

# test number #1
# Execute three POST /dishes requests using the dishes, “orange”, “spaghetti”,
# and “apple pie”. The test is successful* if (i) all 3 requests return unique
# IDs (none of the IDs are the same), and (ii) the return status code from
# each POST request is 201.
def test_three_post_requests():
    global dishes, dishes_id
    
    i = 0
    for dish in dishes:
        response = requests.post('http://127.0.0.1:8000/dishes',
                                 headers={"Content-Type": "application/json"},
                                 json={"name": dish})
        dishes_id[i] = response.json()
        assert response.status_code == 201
        i+=1

    assert len(set(dishes_id)) == 3

# test number #2
# Execute a GET dishes/<orange-ID> request, using the ID of the orange dish.
# The test is successful if (i) the sodium field of the return JSON object is
# between .9 and 1.1 and (ii) the return status code from the request is 200.
def test_get_orange_id_request():
    global dishes_id
    response = requests.get(f'http://127.0.0.1:8000/dishes/{dishes_id[0]}',
                           headers={"Content-Type": "application/json"})
    sodium = response.json()["sodium"]
    assert sodium is not None and 0.9 <= sodium <= 1.1
    assert response.status_code == 200

# test number #3
# Execute a GET /dishes request. The test is successful if (i) the returned
# JSON object has 3 embedded JSON objects (dishes), and (ii) the return status
# code from the GET request is 200
def test_get_request():
    response = requests.get('http://127.0.0.1:8000/dishes',
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 200
    assert len(response.json()) == 3

# test number #4
# Execute a POST /dishes request supplying the dish name “blah”.
# The test is successful if (i) the return value is -3,
# and (ii) the return code is 404 or 400 or 422.
def test_invalid_name_dish_post_request():
    response = requests.post('http://127.0.0.1:8000/dishes',
                             headers={"Content-Type": "application/json"},
                             json={"name": "blah"})

    assert response.json() == -3
    assert response.status_code in [400, 404, 422]

# test number #5
# Perform a POST dishes request with the dish name “orange”.
# The test is successful if (i) the return value is -2 (same dish name as 
# existing dish), and (ii) the return status code is 400 or 404 or 422. 
def test_exist_name_dish_post_request():
    response = requests.post('http://127.0.0.1:8000/dishes',
                             headers={"Content-Type": "application/json"},
                             json={"name": "orange"})

    assert response.json() == -2
    assert response.status_code in [400, 404, 422]

# test number #6
# Perform a POST /meals request specifying that the meal name is “delicious”,
# and that it contains an “orange” for the appetizer, “spaghetti” for the
# main, and “apple pie” for the dessert (note you will need to use their dish
# IDs). The test is successful if (i) the returned ID > 0 and (ii) the
# return status code is 201.
def test_meals_post_request():
    global dishes_id, meal_id
    meal = {
        "name": "delicious",
        "appetizer": dishes_id[0],
        "main": dishes_id[1],
        "dessert": dishes_id[2]
    }
    response = requests.post("http://127.0.0.1:8000/meals",
                             headers={"Content-Type": "application/json"},
                             json=meal)
    meal_id = response.json()
    assert response.status_code == 201
    assert response.json() > 0

# test number #7
def test_get_meals_request():
    response = requests.get( "http://127.0.0.1:8000/meals",
                           headers={"Content-Type": "application/json"})
    meals = response.json()
    assert len(response.json()) == 1
    assert response.status_code == 200

    meal = meals[str(meal_id)]
    cal = meal["cal"]
    
    assert cal is not None and 400 <= cal <= 500

# test number #8
def test_exist_meals_post_request():
    global dishes_id
    meal = {
        "name": "delicious",
        "appetizer": dishes_id[0],
        "main": dishes_id[1],
        "dessert": dishes_id[2]
    }
    response = requests.post("http://127.0.0.1:8000/meals",
                             headers={"Content-Type": "application/json"},
                             json=meal)
    assert response.json() == -2
    assert response.status_code in [400, 422]
