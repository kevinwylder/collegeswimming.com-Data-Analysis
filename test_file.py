from bs4 import BeautifulSoup
import urllib.request
import re
import json
import sys
from bs4 import BeautifulSoup
from helperfunctions import to_event_title
import time


def get_team_results(team_id, season):
    """
    :param team_id: integer id of the team to collect meets for (e.g. 184)
    :param season: string season from which you are collecting meets (e.g. "2018-2019")
    :return: meets: dictionary of meet ids, names, and dates (for the purpose of filling in date slot in relays)
    """
    url = "https://www.collegeswimming.com/team/{}/results/?page=1&name=&meettype=&season={}".format(team_id, season)
    try:
        page = urllib.request.urlopen(url)
        source = page.read()
    except urllib.request.HTTPError as e:
        print(e) # otherwise print out the error and return empty tuple
        return ([],"")
    soup = BeautifulSoup(source, 'html.parser')
    print("getting meets for team {} during season {}".format(team_id, season))
    # meets["team_name"] = soup.find("h1", class_="c-toolbar__title").text

    meets = {}
    meet_list = soup.find("section", class_="c-list-grid")
    for meet in meet_list.find_all("a"):
        meet_id = meet["href"].split("/")[-1]
        meet_name = meet.find("h3").text
        meet_submitted = "Completed" in meet.find("ul",
                                                  class_="c-list-grid__meta o-list-inline o-list-inline--dotted").text
        meet_date = meet.find("time")["datetime"]

        meets[meet_id] = {"meet_name": meet_name, "meet_date": meet_date, "submitted": meet_submitted}
    print(meets)
    return meets


def get_meet_event_ids(meet, gender):
    """
    :param meet: the id used for this meet
    :param gender: character M,F,X representing gender (male, female, mixed) to get events for
    :return: event_id_dict: dictionary of event id's to event names in a meet
    #TODO: get this to work without a gender input
        #NOTE: if gender is not specified, it goes to a default gender (or last one you looked at on any page)
            # if a gender IS specified but it isn't in that meet, it will instead load W, M, or X (in that order)
            # simple solution is to just load page three times and live with time wasted overwriting dictionary values
    """
    url = "https://www.collegeswimming.com/results/{}/?gender={}".format(meet, gender)
    try:
        page = urllib.request.urlopen(url)
        source = page.read()
    except urllib.request.HTTPError as e:
        print(e)  # otherwise print out the error and return empty tuple
        return {}
    soup = BeautifulSoup(source, 'html.parser')
    print("getting event_ids for meet {} for gender {}".format(meet, gender))
    # meets["team_name"] = soup.find("h1", class_="c-toolbar__title").text

    event_id_dict = {}
    event_list = soup.find("ul", class_="c-sticky-filters__list o-list-block o-list-block--divided js-max-height")
    if event_list is not None:
        for event in event_list.find_all("div", class_="o-media o-media--flush"):
            event = event.find("div", title="Completed")
            event_id = int(re.sub("[^0-9]", "", event.text))
            event_name = event.find_next_sibling("div").text
            event_id_dict[event_name] = event_id
        print(event_id_dict)
        return event_id_dict
    else:
        print("meet {} not submitted".format(meet))
        return {"MEET NOT SUBMITTED": 0}


# you could also do this by looking it up by team, then you just have to visit every meet.
def get_relay_leg_times(team_id, meet_id, relay_id):
    """
    :param team_id: the team whose data you want to collect for the given relay event
    :param meet_id: the id of the meet they competed in
    :param relay_id: the id for the relay event at that particular meet
    """

    # get IDs of the swimmers on a university's relay team(s)
    url = "https://www.collegeswimming.com/results/{}/event/{}/".format(meet_id, relay_id)
    try:
        page = urllib.request.urlopen(url)
        source = page.read()
    except urllib.request.HTTPError as e:
        print(e)  # otherwise print out the error and return empty tuple
        return ([],[])
    soup = BeautifulSoup(source, "html.parser")

    swimmer_id_list = []
    times = []
    team_instances = soup.find_all("a", href="/team/{}".format(team_id))  # find out actual name for relay teams
    for team in team_instances:
        if len(team.attrs) == 1:
            if "DQ" in team.find_parent('td').find_next_sibling().text:
                print("excluding disqualified team.")
                continue
            table_soup = team.find_next_sibling('ol')
            for swimmer in table_soup.find_all('a'):
                swimmer_id_list.append(swimmer['href'].split('/')[2])
            # get the split times of the 4 swimmers on a relay team
            splash_split_id = team.find_parent('td').find_next_sibling().find('abbr')['id'][4:]
            splash_splits_url = "https://www.collegeswimming.com/times/{}/splashsplits/".format(splash_split_id)
            try:
                page = urllib.request.urlopen(splash_splits_url)
                splash_source = page.read()
            except urllib.request.HTTPError as e:
                print(e) # otherwise print out the error and return empty tuple
                return ([],[])

            splash_soup = BeautifulSoup(splash_source,"html.parser").tbody
            if splash_soup is None:
                print("no splits available for meet {}".format(meet_id))
                return []
            for row in splash_soup.find_all("tr"):
                if row.find_all("td")[3].text[0].isdigit():  # in relays longer than 200Y, not all rows have leg times.
                    times.append(row.find_all("td")[3].text)  # this is the leg time for a given swimmer.
        else:
            continue
    print(swimmer_id_list)
    print(times)
    return list(zip(swimmer_id_list, times))


def get_relay_swim_data(team_to_pull, gender_to_pull, season_to_pull, relays_to_pull):
    """
    :param team_to_pull: the ID number of the team whose data is being collected
    :param gender_to_pull: a character M,F,X representing Male, Female, or Mixed
    :param season_to_pull: a string representing the season/year the data is being pulled from
    :param relays_to_pull: List of relay events to pull. (e.g. MM200 = Men's 200 Yard Medley Relay)
    :return: 2D list where rows are individual swims and columns are in following format:
    [swimmer_id, team_id, time, 0, meet_id, gender, event_code, date, 0, snapshot_id]
    """
    def medley():
        medley_leg_dict = {1: "BS", 2: "BR", 3: "BF"}
        for i in range(len(relay_results)):
            if i%4 is not 0:
                medley_leg_name = str(int(relay_string[1:-1])//4) + medley_leg_dict[i%4] + "_R"
                relay_swims.append([relay_results[i][0], team_to_pull, relay_results[i][1], 0, meet_id, relay_string[0],
                                   medley_leg_name, meets[meet_id]["meet_date"]])

    def freestyle():
        for i in range(len(relay_results)):
            if i % 4 != 0:
                freestyle_leg_name = str(int(relay_string[1:-1])//4) + "F_R"
                relay_swims.append([relay_results[i][0], team_to_pull, relay_results[i][1], 0, meet_id, relay_string[0],
                                   freestyle_leg_name, meets[meet_id]["meet_date"]])

    relay_swims = []
    meets = get_team_results(team_to_pull, season_to_pull)  # can have this work the same way that get_swim_data does later if that helps
    list_of_meets = list(meets.keys())

    for meet_id in list_of_meets:
        if meets[meet_id]["submitted"]:
            meets[meet_id]["events"] = get_meet_event_ids(meet_id, gender_to_pull)
            for relay_string in relays_to_pull:
                event_name = to_event_title(gender_to_pull + relay_string)
                if event_name in meets[meet_id]["events"]:
                    relay_results = get_relay_leg_times(team_to_pull, meet_id, meets[meet_id]["events"][event_name])
                    if relay_string[0] is "M":
                        medley()
                    elif relay_string[0] is "F":
                        freestyle()
        else:
            print("Results for {} not submitted".format(meets[meet_id]["meet_name"]))
    return relay_swims


#print(list_of_meets)
#for meet_id in list_of_meets:
#    meets[meet_id]["events"] = get_meet_event_ids(meet_id, "M")
#    if "200 Medley Relay Men " in meets[meet_id]["events"]:
#        results = get_relay_leg_times(184, meet_id, meets[meet_id]["events"]["200 Medley Relay Men "])
#        for index in results:
#            thebiglist.append([index[0], 184, index[1], 0, meet_id, "M", "M800Y", meets[meet_id]["meet_date"]])
relay_swims = get_relay_swim_data(184, "M", "2018-2019",["M200Y", "F200Y"])
for swim in relay_swims:
    print(swim)

# swimmer_id, team_id, time, 0, meet_id, gender, event_code, date, 0, snapshot_id)