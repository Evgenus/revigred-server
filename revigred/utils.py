import random

NAMES = [
    "James", "Christopher", "Ronald", "Mary", "Lisa", "Michelle", "John", 
    "Daniel", "Anthony", "Patricia", "Nancy", "Laura", "Robert", "Paul", 
    "Kevin", "Linda", "Karen", "Sarah", "Michael", "Mark", "Jason", "Barbara", 
    "Betty", "Kimberly", "William", "Donald", "Jeff", "Elizabeth", "Helen", 
    "Deborah", "David", "George", "Jennifer", "Sandra", "Richard", "Kenneth", 
    "Maria", "Donna", "Charles", "Steven", "Susan", "Carol", "Joseph", 
    "Edward", "Margaret", "Ruth", "Thomas", "Brian", "Dorothy", "Sharon",
    ]

SURNAMES = [
    "Smith", "Anderson", "Clark", "Wright", "Mitchell", "Johnson", "Thomas", 
    "Rodriguez", "Lopez", "Perez", "Williams", "Jackson", "Lewis", "Hill", 
    "Roberts", "Jones", "White", "Lee", "Scott", "Turner", "Brown", "Harris", 
    "Walker", "Green", "Phillips", "Davis", "Martin", "Hall", "Adams", 
    "Campbell", "Miller", "Thompson", "Allen", "Baker", "Parker", "Wilson", 
    "Garcia", "Young", "Gonzalez", "Evans", "Moore", "Martinez", "Hernandez", 
    "Nelson", "Edwards", "Taylor", "Robinson", "King", "Carter", "Collins",
    ]

def get_random_name():
    name = random.choice(NAMES)
    surname = random.choice(SURNAMES)
    return name + " " + surname

def title(text, char="=", size=79):
    length = len(text)
    first = int((size - length)/2 - 3)
    last = size - 6 - first - length
    return '# ' + (char*first) + ' ' + text + ' ' + (char*last) + ' #'