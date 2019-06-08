import urllib.request
import json
import sqlite3
import random
import sys
from constants import *
from helperfunctions import *
from team_dict.team_dict import *
from bs4 import BeautifulSoup
#import datetime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# College Swimming Summer Break Project 2019                                Brad Beacham #
#                                                      Adapted from code by Kevin Wylder #
# This file builds a database from data collected off collegeswimming.com                #
# for more detail on the structure of the database, the global variables in this file,   #
# or the collegeswimming.com website structure, see the README                           #
#                                                                                        #
# From here on out, 90 character width isn't guarenteed                                  #
 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# URL's for pulling data from
SWIMMER_URL = "https://www.collegeswimming.com/swimmer/{}"
SWIMMER_EVENT_URL = "https://www.collegeswimming.com/swimmer/{}/times/byeventid/{}"
ROSTER_URL = "https://www.collegeswimming.com/team/{}/roster?season={}&gender={}"

# Missing data in createXYZTable is filled in by data put into insertXYZCommand using .format()
CREATE_SWIMS_TABLE = "CREATE TABLE IF NOT EXISTS Swims (swimmer INTEGER, team INTEGER, time REAL, scaled REAL, meet_id INTEGER, event TEXT, date INTEGER, taper INTEGER, snapshot INTEGER);"
INSERT_SWIM_COMMAND = "INSERT INTO Swims VALUES({}, {}, {}, {}, {}, '{}{}', {}, {}, {});"
CREATE_SNAPSHOT_TABLE_COMMAND = "CREATE TABLE IF NOT EXISTS Snapshots (snapshot INTEGER, date TEXT, teams TEXT, events TEXT);"
INSERT_SNAPSHOT_COMMAND = "INSERT INTO Snapshots VALUES({}, '{}', '{}', '{}');"
CREATE_NAME_TABLE = "CREATE TABLE IF NOT EXISTS {} (name TEXT, id INTEGER);"
CHECK_NAME_TABLE = 'SELECT id FROM {} WHERE id={} LIMIT 1;'
ADD_TO_NAME_TABLE = "INSERT INTO {} VALUES('{}', {});"


def request_swimmer(swimmer_id, event, search_start_timestamp, search_end_timestamp):
    """
    Input a swimmerID and event.
    Output list of tuples containing event swim's in a tuple containing the date
    they participated in the event and the time they achieved while competing.
    tuple format is (date, swimtime)
    """
    swimmer_data = []
    swimmer_events = []
    url = SWIMMER_URL.format(swimmer_id)
    try:  # to open a url for that swimmer and read their data
        page = urllib.request.urlopen(url)
        source = page.read()
    except urllib.request.HTTPError as e:
        print(e)  # otherwise print out the error and return empty tuple
        return ([],"")
    soup = BeautifulSoup(source, 'html.parser')
    selection = soup.find("select", class_="form-control input-sm js-event-id-selector")
    if selection:
        for eventOption in selection.find_all("option", class_="event"):
            swimmer_events.append(eventOption["value"])

    # If the event you want data on is contained within the list of events they have data for that swimmer on, then add
    # that data to swimmer_data
    if event in swimmer_events:
        url = SWIMMER_EVENT_URL.format(swimmer_id, event)
        page = urllib.request.urlopen(url)
        source = page.read()
        event_history = json.loads(source)
        for swim in event_history:
            # convert the date string to epoch
            split_date = swim["dateofswim"].split("-")
            date = convert_to_time(int(split_date[0]), int(split_date[1]), int(split_date[2]))
            if search_start_timestamp < date < search_end_timestamp:
                # ^^ defined below the timestamp function and updated every year loop
                swim_list = [date, swim["time"], swim["meet_id"]]
                swimmer_data.append(swim_list)
    return swimmer_data


def get_roster(team_id, season, gender):
    """
        Input: a team_id, season, and gender used to uniquely identify a team
        Output: List of tuples containing swimmer names and IDs
    """
    team = {}
    #gets a list of (Name, swimmer_id) tuples and the team name for a given team_id
    url = ROSTER_URL.format(team_id, season, gender)
    try:
        page = urllib.request.urlopen(url)
        source = page.read()
    except urllib.request.HTTPError as e:
        print(e) # otherwise print out the error and return empty tuple
        return ([],"")
    soup = BeautifulSoup(source, 'html.parser')
    team["name"] = soup.find("h1", class_="c-toolbar__title").text

    table_body = soup.find("table", class_="c-table-clean c-table-clean--middle c-table-clean--fixed table table-hover").tbody
    team["roster"] = []
    for tableRow in table_body.find_all("tr"):
        swimmer_id = tableRow.td.a["href"].split("/")[-1]
        swimmer_name = normalize_name(str(tableRow.td.strong.text))
        team["roster"].append((swimmer_name, swimmer_id))
    return team


def get_swim_data(teams_to_pull, genders_to_pull,
                  year_start, year_end,
                  events_to_pull = DEFAULT_EVENTS_TO_PULL,
                  database_file_name = DATABASE_FILE_NAME, ):
    # open the sqlite database
    for team in range(len(teams_to_pull)):
        teams_to_pull[team] = TEAM_DICT[teams_to_pull[team]]
    
    connection = sqlite3.connect(database_file_name)
    cursor = connection.cursor()

    # add information about this snapshot to the Snapshots table (and create it if it doesn't exist)
    cursor.execute(CREATE_SNAPSHOT_TABLE_COMMAND)
    snapshot_id = random.randint(0, 4294967295)  # what are the odds? 100% I'm a lazy programmer << NOTE: change this
    date_range_string = "{0}.{1}.{2}-{3}.{1}.{2}".format(year_start, SEASON_LINE_MONTH, SEASON_LINE_DAY, year_end)
    # ^^ creates a string representing a range of dates equal to year_end-year_start years
    teams_string = ",".join(str(team) for team in teams_to_pull)
    events_string = ",".join(events_to_pull)
    cursor.execute(INSERT_SNAPSHOT_COMMAND.format(snapshot_id, date_range_string, teams_string, events_string))

    # ensure the existence of each event table and the Teams/Swimmers tables
    cursor.execute(CREATE_SWIMS_TABLE)
    cursor.execute(CREATE_NAME_TABLE.format("Swimmers"))
    cursor.execute(CREATE_NAME_TABLE.format("Teams"))
    
    # retrieve and add the times to the database
    for simple_year in range(year_start, year_end):   # for each competition year
        season_string = str(simple_year) + "-" + str(simple_year + 1)
        print("Collecting Season {}".format(season_string))
        search_start_timestamp = convert_to_time(int(simple_year), SEASON_LINE_MONTH, SEASON_LINE_DAY)
        search_end_timestamp = convert_to_time(int(simple_year) + 1, SEASON_LINE_MONTH, SEASON_LINE_DAY)
        team_counter = 0
        percent = 0
        for team_id in teams_to_pull:   # for each team
            for gender in genders_to_pull:  # for each gender
                # pull the roster for this season and gender
                team = get_roster(team_id, season_string, gender)
                print (team)
                # add team to the Teams table
                if not team["name"] is "":  # if there wasn't a 404 error
                    matches = cursor.execute(CHECK_NAME_TABLE.format("Teams", team_id))
                    if matches.fetchone() is None:  # if there are no duplicates
                        cursor.execute(ADD_TO_NAME_TABLE.format("Teams", team["name"], team_id))
                for index, swimmer in enumerate(team["roster"]):
                    print (swimmer[0] + " " + swimmer[1])  # for each swimmer on the team
                    # enumerate this loop to have an index for the loading bar
                    percent_of_team = float(index) / float(len(team["roster"]))
                    show_loading_bar(percent + (percent_of_team / float(len(teams_to_pull))))
                    # add the swimmer to the Names table
                    matches = cursor.execute(CHECK_NAME_TABLE.format("Swimmers", swimmer[1]))
                    if matches.fetchone() is None:
                        cursor.execute(ADD_TO_NAME_TABLE.format("Swimmers", sqlsafe(swimmer[0]), swimmer[1]))
                    for event in events_to_pull:   # for each of this swimmer's event we're searching
                        print (swimmer[1] + " " + event)
                        swims = request_swimmer(swimmer[1], event, search_start_timestamp, search_end_timestamp)
                        sys.stdout.flush()
                        for swim in swims:   # for each qualified race
                            # add this race to the database
                            command = INSERT_SWIM_COMMAND.format(swimmer[1], team_id, swim[1], 0, swim[2], gender, event, swim[0], 0, snapshot_id)
                            cursor.execute(command)
                # print the loading bar
                team_counter += 1
                percent = float(team_counter) / float(len(teams_to_pull))
                show_loading_bar(percent)
        connection.commit()

    get_event_times = "SELECT time FROM Swims WHERE event='{}{}' AND date>{} AND date<{}"#I can update this a bit (See notes)
    update_with_scaled = "UPDATE Swims SET scaled={} WHERE event='{}{}' AND date>{} AND date<{} AND time={}"
    # fill out the scaled column
    print ("Scaling times")
    # convert each swim to a season z-score
    for simple_year in range(year_start, year_end):   # for each competition year
        season_start_timestamp = convert_to_time(int(simple_year), SEASON_LINE_MONTH, SEASON_LINE_DAY)
        season_end_timestamp = convert_to_time(int(simple_year) + 1, SEASON_LINE_MONTH, SEASON_LINE_DAY)
        for event in events_to_pull:
            for gender in genders_to_pull:
                cursor.execute(get_event_times.format(gender, event, season_start_timestamp, season_end_timestamp))
                times = [x[0] for x in cursor.fetchall()]
                try:
                    average = sum(times) / len(times)
                except ZeroDivisionError as e:
                    print("No data was available on event {}".format(event))
                    continue
                print ("average for {}{} in {}: {}".format(gender, event, simple_year, average))
                sd = (sum([(x - average)**2 for x in times]) / len(times)) ** .5  # standard deviation
                update_list = [(x, (x - average) / sd) for x in times]
                for update in update_list:
                    command = update_with_scaled.format(update[1], gender, event, season_start_timestamp,
                                                        season_end_timestamp, update[0])
                    cursor.execute(command)
    connection.commit()
    print ("scaled")


    print ("")
    print ("Finding taper swims")
    for simple_year in range(year_start, year_end):
        season_start_timestamp = convert_to_time(int(simple_year), SEASON_LINE_MONTH, SEASON_LINE_DAY)
        season_end_timestamp = convert_to_time(int(simple_year) + 1, SEASON_LINE_MONTH, SEASON_LINE_DAY)
        print ("Season {}-{}".format(simple_year, simple_year + 1))
        print ("From timestamp {} to {}".format(season_start_timestamp, season_end_timestamp))
        for team_id in teams_to_pull:
            # get a list of all the days this team swam
            cursor.execute("SELECT date FROM Swims WHERE team={} AND date>{} AND date<{}".format(team_id,
                                                                                                 season_start_timestamp,
                                                                                                 season_end_timestamp))
            dates = cursor.fetchall()
            dates = list(set(dates)) # this removes duplicates, which there are many
            meet_scores = []             # populate this with
            average_score = 0
            for date in dates:
                # first check if only one swimmer swam. this is indicative of a glitch where I
                # cannot isolate which roster a swimmer is in if they switched team.
                cursor.execute("SELECT count(*) FROM Swims WHERE team={} AND date={}".format(team_id, date[0]))
                if cursor.fetchone()[0] != 7:
                    # get the average scaled time for this day of swimming and add it to the list
                    cursor.execute("SELECT avg(scaled) FROM Swims WHERE team={} AND date={}".format(team_id, date[0]))
                    meet_tuple = (cursor.fetchone()[0], date[0])
                    average_score += meet_tuple[0]
                    meet_scores.append(meet_tuple)
            average_score /= len(dates)
            for date in meet_scores:
                # a taper swim is a swim at a meet with a below average z-score for that season
                # this can be assumed because, given that a team has dual meets and taper meets
                # online, there will be a two-node normal distribution. the lower node contains
                # taper swims. we'll now update them in the database
                if date[0] < average_score:
                    cursor.execute("UPDATE Swims SET taper=1 WHERE team={} AND date={}".format(team_id, date[1]))
                else:
                    cursor.execute("UPDATE Swims SET taper=2 WHERE team={} AND date={}".format(team_id, date[1]))

    print ("Finding outliers")
    cursor.execute("UPDATE Swims SET taper=3 WHERE scaled>3")  # a lazy solution. I'm tired << let's fix that

    connection.commit()
    connection.close()


# The function below will be removed and replaced with a better version somewhere else
def inputs_for_swim_data_search(all_default = False):
    """
        allows you to input test values for
        """
    if (all_default == True):
        events_to_pull = DEFAULT_EVENTS_TO_PULL
        genders_to_pull = DEFAULT_GENDER
        teams_to_pull = DEFAULT_TEAMS_TO_PULL
        year_start = DEFAULT_YEAR_START
        year_end = DEFAULT_YEAR_END
        database_file_name = DATABASE_FILE_NAME
    else:
        database_file_name = input("Use default database file? Y/N ")
        if database_file_name == "Y":
            database_file_name = DATABASE_FILE_NAME
        else:
            database_file_name = input("Type database file name here: ")
        # events_to_pull = input("Which events would you like to pull information on? Separate with spaces please ").split()
        teams_to_pull = []
        temp_val = input("Input colleges whose teams you would like to pull one at a time. "
                         "Hit \"return\" after each entry.\n1. ")
        while temp_val != ("done" or "Done"):
            teams_to_pull.append(temp_val)
            temp_val = input("\n{}. ".format(len(teams_to_pull)+1))
        genders_to_pull = input("M, F, or M F? ").split()
        year_start = eval(input("Input start year"))
        year_end = eval(input("Input end year"))
        events_to_pull = DEFAULT_EVENTS_TO_PULL
    return get_swim_data(teams_to_pull, genders_to_pull, year_start, year_end, events_to_pull, database_file_name)


def main():
    inputs_for_swim_data_search(False)


main()
