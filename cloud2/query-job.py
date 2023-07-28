import requests

def get_request(id):
    dish_id = int(id)
    response = requests.get(f'http://127.0.0.1:8000/dishes/{dish_id}',
                            headers={"Content-Type": "application/json"})
    if response.status_code == 200:
        return [response.json()["cal"], response.json()["sodium"], response.json()["sugar"]]
    else:
        return [response.status_code, response.json()]

def post_request(dish):
    response = requests.post('http://127.0.0.1:8000/dishes',
                             headers={"Content-Type": "application/json"},
                             json={"name": dish})
    if response.status_code == 201:
        return [response.json()]
    else:
        return [response.status_code, response.json()]
        

def read_from_file():
    response_file = open('/tmp/response.txt', 'w')
    with open('query.txt', 'r') as file:
        for line in file:
            line = line.rstrip('\n')
            dish_id = post_request(line)
            if len(dish_id) == 1:
                ls = get_request(dish_id[0])
                if len(ls) == 3:
                    string = line + " contains " + '{:1f}'.format(ls[0]) + " calories, " + '{:1f}'.format(ls[1]) + " mgs of sodium, and " \
                            + '{:1f}'.format(ls[2]) + " grams of sugar\n"
                    response_file.write(string)
                elif len(ls) == 2:
                    response_file.write("ERROR\n")
            else:
                response_file.write("ERROR\n")

        response_file.close()



def main():
    read_from_file()



if __name__ == "__main__":
    main()
