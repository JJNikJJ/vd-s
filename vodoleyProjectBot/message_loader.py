import json


def get_messages():
    with open('messages.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data
