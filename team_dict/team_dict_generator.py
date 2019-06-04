import urllib.request
from bs4 import BeautifulSoup
from constants import *


def create_team_dict():
    team_dict = {}
    team_id_counter = 1
    while team_id_counter < MAX_TEAM_ID + 1:
        'gets a list of (Name, swimmerId) tuples and the team name for a given teamId'
        url = TEAM_URL.format(team_id_counter)
        try:
            page = urllib.request.urlopen(url)
            source = page.read()
        except urllib.request.HTTPError as e:
            print(e)
            team_id_counter = team_id_counter + 1
            continue

        soup = BeautifulSoup(source, 'html.parser')
        team_name = soup.find("h1", class_="c-toolbar__title").text
        team_dict[team_name] = team_id_counter
        team_id_counter = team_id_counter + 1
    dict_file = open("team_dict.py","w+")
    dict_file.write("TEAM_DICT = " + str(team_dict))
    dict_file.close()


def confirm_that_you_want_to_run_this():
    answer = input("Running this code takes approximately 1 hour, are you sure that you want to run this? type 'YES' "
                   "(without quotes) if you are certain you wish to run this code")
    if answer == "YES":
        create_team_dict()
    else:
        print("Cancelling")


confirm_that_you_want_to_run_this()

# this was used to fix key values when the the counter was wrong. I decided to keep it commented here just in case that
# ever happened again.
# import team_dict
# def fixVals():
#    print(team_dict.TEAM_DICT)
#    apples = team_dict.TEAM_DICT
#    for key, value in apples.items():
#        apples[key] = value - 1
#    print(apples)
#    dict_file = open("team_dict.py","w+")
#    dict_file.write("TEAM_DICT = " + str(apples))
#    dict_file.close()
