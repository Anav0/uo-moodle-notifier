import requests
import re
import sys
from datetime import datetime
import time
import os
from pathlib import Path


class Assigment:
    def __init__(self, id, name, link):
        self.id = id
        self.name = name
        self.link = link

    def __str__(self):
        return '{} {} {}'.format(self.id, self.name, self.link)


def login(username, password, session):
    login_url = "https://moodle.math.uni.opole.pl/login/index.php"
    login_html = session.get(login_url).text
    login_html_request = re.findall(
        "name=\"logintoken\" value=\"(.*)\"", login_html)
    if(len(login_html_request) <= 0):
        sys.exit("Could not get login token")
    login_token = login_html_request[0]
    payload = {
        "anchor": "",
        "username": username,
        "password": password,
        "logintoken": login_token
    }
    header = {"Content-type": "application/x-www-form-urlencoded",
              "Accept": "text/plain"}
    login_response = session.post(login_url, data=payload, headers=header)


def search_for_assigments(course_page_url, session):
    course_html = session.get(course_page_url).text
    search_result = re.findall(
        "<li class=\"activity assign modtype_assign \".*?>.*?(https://moodle.math.uni.opole.pl/mod/assign/view.php\?id=(.*?))\".*?<span class=\"instancename\">(.*?)<span.*?</li>", course_html)

    assigments = []

    for group in search_result:
        assigments.append(Assigment(group[1], group[2], group[0]))

    return assigments


def get_course_name(course_page_url, session):
    course_html = session.get(course_page_url).text
    course_name_regex = 'class="page-header-headings"><h1>(.*)</h1></div>'

    course_name_search = re.findall(course_name_regex, course_html)

    if(len(course_name_search) <= 0):
        return ''
    else:
        return course_name_search[0]


def store_assigments_id(ids, filePath):
    with open(filePath, 'w') as file:
        content = ""
        for id in ids:
            content += str(id)+os.linesep
        file.write(content)


def get_assigments_id(filePath):
    ids = []
    with open(filePath, 'r') as file:
        for line in file:
            ids.append(line.rstrip(os.linesep))
    return ids


def create_if_not_exist(file_path):
    Path(file_path).parent.mkdir(parents=True, exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, "w"):
            pass


def print_course_name(course_page_url, session):
    course_name = get_course_name(course_page_url, session)
    if len(course_name) > 0:
        print('Nazwa kursu: {}'.format(course_name))
    else:
        print('Nie znaleziono nazwy kursu')


def get_ids_of_assigment(assigments):
    ids = []
    for assigment in assigments:
        ids.append(assigment.id)
    return ids


def get_arr_diff(arr1, arr2):
    return (list(list(set(arr1)-set(arr2)) + list(set(arr2)-set(arr1))))


def main(args):
    if len(args) < 2:
        sys.exit("Nie podano argumentów: username password course_id interval?")

    username = args[0]
    password = args[1]
    course_id = args[2]
    checking_interval_sec = 5

    file_path = os.path.join(os.path.expanduser(
        '~'), 'Documents', 'moodle-notifier', 'course-{}.txt'.format(course_id))

    if len(args) > 3:
        checking_interval_sec = args[3]

    course_page_url = "https://moodle.math.uni.opole.pl/course/view.php?id={}".format(
        course_id)

    session = requests.session()

    login(username, password, session)

    print_course_name(course_page_url, session)

    create_if_not_exist(file_path)

    current_assigments_ids = get_assigments_id(file_path)

    while True:
        print('')

        current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        course_html = session.get(course_page_url).text
        if len(re.findall("Przyjmowanie cookies", course_html)) > 0:
            login(username, password, session)

        assigments = search_for_assigments(
            course_page_url, session)

        assigments_ids = get_ids_of_assigment(assigments)

        if len(get_arr_diff(assigments_ids, current_assigments_ids)) != 0:
            print('Ilość zadań uległa zmianie - {}'.format(current_date))
            [print(assigment) for assigment in assigments]
            store_assigments_id(assigments_ids, file_path)
            current_assigments_ids = assigments_ids
        else:
            print('Brak nowych zadań - {}'.format(current_date))

        time.sleep(checking_interval_sec)


if __name__ == "__main__":
    main(sys.argv[1:])
