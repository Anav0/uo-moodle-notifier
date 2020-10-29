import requests
import re
import sys
from datetime import datetime
import time


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
    return re.findall("<li class=\"activity assign modtype_assign \".*?>.*?<span class=\"instancename\">(.*?)<span.*?</li>", course_html)


def get_course_name(course_page_url, session):
    course_html = session.get(course_page_url).text
    course_name_regex = 'class="page-header-headings"><h1>(.*)</h1></div>'

    course_name_search = re.findall(course_name_regex, course_html)

    if(len(course_name_search) <= 0):
        return ''
    else:
        return course_name_search[0]


def main(args):
    if len(args) < 2:
        sys.exit("Nie podano argumentów: username password course_id interval?")

    username = args[0]
    password = args[1]
    course_id = args[2]
    checking_interval_sec = 5*60

    if len(args) > 3 != None:
        checking_interval_sec = args[3]

    course_page_url = "https://moodle.math.uni.opole.pl/course/view.php?id={}".format(
        course_id)

    session = requests.session()

    login(username, password, session)

    course_name = get_course_name(course_page_url, session)
    if len(course_name) > 0:
        print('Nazwa kursu: {}'.format(course_name))
    else:
        print('Nie znaleziono nazwy kursu')

    init_search_results = search_for_assigments(course_page_url, session)

    current_number_of_assigments = len(init_search_results)
    print('')
    print('Obecna ilość zadań: {}'.format(current_number_of_assigments))
    [print(assigment) for assigment in init_search_results]

    while True:
        time.sleep(checking_interval_sec)
        print('')

        current_date = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        course_html = session.get(course_page_url).text

        if len(re.findall("Przyjmowanie cookies", course_html)) > 0:
            login(username, password, session)

        assigment_search_result = search_for_assigments(
            course_page_url, session)

        number_of_assigments = len(assigment_search_result)

        if number_of_assigments > current_number_of_assigments:
            print('Nowe zadanie - {}'.format(current_date))
            [print(assigment) for assigment in number_of_assigments]
        else:
            print('Brak nowych zadań - {}'.format(current_date))


if __name__ == "__main__":
    main(sys.argv[1:])
