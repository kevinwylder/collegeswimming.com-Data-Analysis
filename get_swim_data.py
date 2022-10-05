import urllib.request
import json
import sqlite3
import random
import re
from constants import *
from helperfunctions import *
from team_dict import *
from bs4 import BeautifulSoup

########################################################################################################################
# College Swimming Summer Break Project 2019                                                              Brad Beacham #
#                                                                                    Adapted from code by Kevin Wylder #
# This file builds a database from data collected off collegeswimming.com for more detail on the structure of the      #
# database, the global variables in this file, or the collegeswimming.com website structure, see the README or         #
# constants file                                                                                                       #
#                                                                                                                      #
# From here on out, 120 character width isn't guaranteed, but is usually followed                                      #
########################################################################################################################


def request_swimmer(swimmer_id, event, search_start_timestamp, search_end_timestamp):
    """
    :param swimmer_id: Integer ID number of a specific swimmer
    :param event: the code used for classifying a given event
    :param search_start_timestamp: integer timestamp representing the beginning of the time frame we are collecting
    data from
    :param search_end_timestamp: integer timestamp representing the end of the time frame we are collecting data from
    :return swimmer_data: a 2-D array where the first column is the date a swim took place, second column is the time
    achieved by the swimmer in that event, and the third column is the numerical ID of the meet they were competing in.
    """
    swimmer_data = []
    swimmer_events = []  # This will be filled with the list of all events that this swimmer has participated in
    url = SWIMMER_URL.format(swimmer_id)
    try:  # to open a url for that swimmer and read their data
        page = urllib.request.urlopen(url)
        source = page.read()
    except urllib.request.HTTPError as e:
        print(e)  # otherwise print out the error and return empty list
        return [[0,0,0]]
    soup = BeautifulSoup(source, 'html.parser')
    selection = soup.find("select", class_="form-control input-sm js-event-id-selector")
    if selection:
        for eventOption in selection.find_all("option", class_="event"):
            swimmer_events.append(eventOption["value"])

    # If the event you want data on is contained within the list of events that swimmer has participated in, then add
    # that data to swimmer_data
    if event in swimmer_events:
        url = SWIMMER_EVENT_URL.format(swimmer_id, event)
        try:  # open and read url containing info on "event" for "swimmer_id"
            page = urllib.request.urlopen(url)
            source = page.read()
        except urllib.request.HTTPError as e:
            print(e)
            return [[0,0,0]]
        event_history = json.loads(source)
        for swim in event_history:
            # convert the date string of a swim to time since epoch (in seconds)
            split_date = swim["dateofswim"].split("-")
            date = convert_to_time(int(split_date[0]), int(split_date[1]), int(split_date[2]))
            # if the swim occurred during desired time frame, add it to swimmer_data
            if search_start_timestamp < date < search_end_timestamp:
                swim_list = [date, swim["time"], swim["meet_id"]]
                swimmer_data.append(swim_list)
    return swimmer_data


def get_roster(team_id, season, gender):
    """
    Input: a team_id, season, and gender used to uniquely identify a team
    Output: List of tuples containing swimmer names and IDs
    :param team_id: integer ID for a team
    :param season: string representing the season we are looking at (e.g. "2017-2018" season)
    :param gender: String M or F representing Men's or Women's roster
    :return team: a dictionary containing the team name and the names and ID's of all team members from the given season
    """
    team = {}
    #gets a list of (Name, swimmer_id) tuples and the team name for a given team_id
    url = ROSTER_URL.format(team_id, gender, season)
    try:  # open the url for the given team_id, season, and gender
        page = urllib.request.urlopen(url)
        source = page.read()
    except urllib.request.HTTPError as e:
        print(e) # otherwise print out the error and return empty tuple
        return {}

    soup = BeautifulSoup(source, 'html.parser')
    # find the team name from BeautifulSoup
    team["name"] = soup.find("h1", class_="c-toolbar__title").text
    # find table containing full team roster from BeautifulSoup
    table_body = soup.find("table", class_="c-table-clean c-table-clean--middle c-table-clean--fixed table table-hover").tbody
    team["roster"] = []
    # add team member names and ids to team dict
    for tableRow in table_body.find_all("tr"):
        swimmer_id = tableRow.td.a["href"].split("/")[-1]
        swimmer_name = normalize_name(str(tableRow.td.strong.text))
        team["roster"].append((swimmer_name, swimmer_id))
    return team


def get_team_results(team_id, season):
    """
    :param team_id: integer id of the team to collect meets for (e.g. 184)
    :param season: string season from which you are collecting meets (e.g. "2018-2019")
    :return meets: dictionary of meet ids, names, and dates (for the purpose of filling in date slot in relays)
    """
    url = RESULTS_URL.format(team_id, season)
    try:  # open url for page containing all meets that given team participated in during given season
        page = urllib.request.urlopen(url)
        source = page.read()
    except urllib.request.HTTPError as e:
        print(e) # otherwise print out the error and return empty tuple
        return {}

    soup = BeautifulSoup(source, 'html.parser')
    print("getting meets for team {} during season {}".format(team_id, season))
    # meets["team_name"] = soup.find("h1", class_="c-toolbar__title").text

    meets = {}
    meet_list = soup.find("section", class_="c-list-grid")  # find list of meets team participated in
    # Add individual meets and data about them to meets dictionary
    for meet in meet_list.find_all("a"):
        meet_id = meet["href"].split("/")[-1]
        meet_name = meet.find("h3").text
        meet_submitted = "Completed" in meet.find("ul",
                                                  class_="c-list-grid__meta o-list-inline o-list-inline--dotted").text
        print("If no data is being collected from meets for relays, it may be because the \"Completed\" "
              "tag is no longer in use")
        split_date = meet.find("time")["datetime"].split("-")
        meet_date = convert_to_time(int(split_date[0]), int(split_date[1]), int(split_date[2]))

        meets[meet_id] = {"meet_name": meet_name, "meet_date": meet_date, "submitted": meet_submitted}
    print(meets)
    return meets


def get_meet_event_ids(meet, gender):
    """
    :param meet: unique integer ID representing a meet
    :param gender: character M,F,X representing gender (male, female, mixed) to get events for
    :return event_id_dict: dictionary of event id's to event names for given meet
    #TODO: get this to work without a gender input
        #NOTE: if gender is not specified, it goes to a default gender (or last one you looked at on any page)
            # if a gender IS specified but it isn't in that meet, it will instead load W, M, or X (in that order)
            # simple solution is to just load page three times and live with time wasted overwriting dictionary values
    """
    url = MEET_URL.format(meet, gender)
    try:  # open url for given meet looking at results for gender
        page = urllib.request.urlopen(url)
        source = page.read()
    except urllib.request.HTTPError as e:
        print(e)  # otherwise print out the error and return empty tuple
        return {}

    soup = BeautifulSoup(source, 'html.parser')
    print("getting event_ids for meet {} for gender {}".format(meet, gender))
    # meets["team_name"] = soup.find("h1", class_="c-toolbar__title").text

    event_id_dict = {}
    # Find list of all events from meet for given gender
    event_list = soup.find("ul", class_="c-sticky-filters__list o-list-block o-list-block--divided js-max-height")
    if event_list is not None:
        # add all events from the meet to event_id_dict
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
    :return relay_leg_times:
    """
    # get IDs of the swimmers on a university's relay team(s)
    url = MEET_EVENT_URL.format(meet_id, relay_id)
    try:  # open url for results of the relay in the meet designated by meet_id and relay_id
        page = urllib.request.urlopen(url)
        source = page.read()
    except urllib.request.HTTPError as e:
        print(e)  # otherwise print out the error and return empty tuple
        return ([],[])
    soup = BeautifulSoup(source, "html.parser")

    swimmer_id_list = []
    times = []
    # find all times that team_id is mentioned in BeautifulSoup
    team_instances = soup.find_all("a", href="/team/{}".format(team_id))  # find out actual name for relay teams
    # get relay leg times by relay team (note that all relay teams checked are from same main team)
    for team in team_instances:
        if len(team.attrs) == 2:  # team names are mentioned multiple times in each row, check for correct column
            # if a team was disqualified, skip it
            if "DQ" in team.find_parent('td').find_next_sibling().text:
                print("excluding disqualified team.")
                continue

            # get list of all 4 swimmers on relay team
            table_soup = team.find_next_sibling('ol')
            for swimmer in table_soup.find_all('a'):
                swimmer_id_list.append(swimmer['href'].split('/')[2])

            # get the split times of the 4 swimmers on a relay team
            splash_split_id = team.find_parent('td').find_next_sibling().find('abbr')['id'][4:]
            splash_splits_url = SPLASH_SPLITS_URL.format(splash_split_id)
            try:  # open url with table of relay split time table
                page = urllib.request.urlopen(splash_splits_url)
                splash_source = page.read()
            except urllib.request.HTTPError as e:
                print(e) # otherwise print out the error and return empty tuple
                return ([],[])

            # add split times, if they were recorded
            # NOTE: this might be an issue if names are available but not splits. see if this is a possible situation
            splash_soup = BeautifulSoup(splash_source,"html.parser").tbody
            if splash_soup is None:
                print("no splits available for meet {}".format(meet_id))
                return []
            for row in splash_soup.find_all("tr"):
                if row.find_all("td")[-1].text[0].isdigit():  # in relays longer than 200Y, not all rows have leg times.
                    times.append(row.find_all("td")[-1].text)  # this is the leg time for a given swimmer.
        else:
            continue
    print(swimmer_id_list)
    print(times)
    relay_leg_times = list(zip(swimmer_id_list, times))
    return relay_leg_times


def get_relay_swim_data(team_to_pull, gender_to_pull, season_to_pull, relays_to_pull):
    """
    :param team_to_pull: the ID number of the team whose data is being collected
    :param gender_to_pull: a character M,F,X representing Male, Female, or Mixed
    :param season_to_pull: a string representing the season/year the data is being pulled from
    :param relays_to_pull: List of relay events to pull. (e.g. MM200 = Men's 200 Yard Medley Relay)
    :return relay_swims: 2D list where rows are individual swims and columns are in following format:
    [swimmer_id, team_id, time, 0, meet_id, gender, event_code, date, 0, snapshot_id]
    which is identical to the format in which new rows are added to swims table
    """
    # used to differentiate between relay teams within a team
    team_letter = {0: "A", 1: "B", 2: "C", 3: "D", 4: "E", 5: "F"}

    # Event is a medley relay, so names relay legs accordingly as events and appends them to relay_swims
    def medley():
        medley_leg_dict = {0: "LM", 1: "2M", 2: "3M", 3: "4M"}
        for i in range(len(relay_results)):
            # NOTE: This assumes teams place exactly as planned
            medley_leg_name = medley_leg_dict[i%4] + str(int(relay_string[1:-1])//4) + team_letter[i//4]
            relay_swims.append([relay_results[i][0], team_to_pull, relay_results[i][1], 0, meet_id, gender_to_pull,
                                medley_leg_name, meets[meet_id]["meet_date"]])

    # Event is freestyle relay, so names relay legs accordingly as events and appends them to relay_swims
    def freestyle():
        for i in range(len(relay_results)):
            if i % 4 != 0:
                # NOTE: This assumes teams place exactly as planned
                freestyle_leg_name = "1F" + str(int(relay_string[1:-1])//4) + team_letter[i//4]
            else:
                freestyle_leg_name = "LF" + str(int(relay_string[1:-1])//4) + team_letter[i//4]

            relay_swims.append([relay_results[i][0], team_to_pull, relay_results[i][1], 0, meet_id, gender_to_pull,
                                freestyle_leg_name, meets[meet_id]["meet_date"]])

    relay_swims = []

    # get full dictionary of meets and their data
    meets = get_team_results(team_to_pull, season_to_pull)  # can have this work the same way that get_swim_data does later if that helps
    list_of_meets = list(meets.keys())

    for meet_id in list_of_meets:
        if meets[meet_id]["submitted"]:
            # add "events" key to meets, containing all events in meet that gender_to_pull participated in
            meets[meet_id]["events"] = get_meet_event_ids(meet_id, gender_to_pull)
            # add data on all relay types in relays_to_pull to relay_swims
            for relay_string in relays_to_pull:
                event_name = to_event_title(gender_to_pull + relay_string)
                if event_name in meets[meet_id]["events"]:
                    # get all relay leg times for team_to_pull in meet meet_id for relay relay_string
                    relay_results = get_relay_leg_times(team_to_pull, meet_id, meets[meet_id]["events"][event_name])
                    if relay_string[0] is "M":
                        medley()
                    elif relay_string[0] is "F":
                        freestyle()
        else:
            print("Results for {} not submitted".format(meets[meet_id]["meet_name"]))
    return relay_swims, meets  # NOTE: can add meets as a return value to use it to make meets database table


def get_swim_data(teams_to_pull, genders_to_pull,
                  year_start, year_end,
                  events_to_pull=DEFAULT_EVENTS_TO_PULL,
                  database_file_name=DATABASE_FILE_NAME, ):
    """
    :param teams_to_pull: List of strings where each string is a swim team (e.g. "Bucknell University")
    :param genders_to_pull: List of characters M, F, representing Male and Female
    :param year_start: Integer value of year to start pulling data from
    :param year_end: Integer value of final year for data pull
    :param events_to_pull: List of event codes for events to pull data on
    :param database_file_name: The name of the database file that information will be stored in
    :return: Nothing is returned. database_file_name will have data written to it, and will be created if it didn't
    exist before.
    """

    # remove relays from events_to_pull for later/separate processing
    relays_to_pull = []
    for event in events_to_pull:
        if event[0] in "MF":
            events_to_pull.remove(event)
            relays_to_pull.append(event)

    # Convert team_dict entries to integer team ID's.
    for team in range(len(teams_to_pull)):
        teams_to_pull[team] = TEAM_DICT[teams_to_pull[team]]

    # open the sqlite database
    connection = sqlite3.connect(database_file_name)
    cursor = connection.cursor()

    # add information about this snapshot to the Snapshots table (and create it if it doesn't exist)
    cursor.execute(CREATE_SNAPSHOT_TABLE_COMMAND)
    snapshot_id = random.randint(0, 4294967295)  # what are the odds? 100% I'm a lazy programmer << NOTE: change this

    # create a Snapshot entry of the new data being pulled. This is essentially a changelog
    date_range_string = "{0}.{1}.{2}-{3}.{1}.{2}".format(year_start, SEASON_LINE_MONTH, SEASON_LINE_DAY, year_end)
    teams_string = ",".join(str(team) for team in teams_to_pull)
    events_string = ",".join(events_to_pull)
    cursor.execute(INSERT_SNAPSHOT_COMMAND.format(snapshot_id, date_range_string, teams_string, events_string))

    # ensure the existence of each event table and the Teams/Swimmers tables
    cursor.execute(CREATE_SWIMS_TABLE)
    cursor.execute(CREATE_SWIMMER_TABLE.format("Swimmers"))
    cursor.execute(CREATE_TEAM_TABLE.format("Teams"))
    cursor.execute(CREATE_MEET_TABLE)
    
    # retrieve and add the times to the database
    for simple_year in range(year_start, year_end):   # for each competition year, do the following
        # THIS IS WHERE SEASON STRING IS MADE AND ROSTER URL BUILDING IS STARTED
        season_string = simple_year - 1996#str(simple_year) + "-" + str(simple_year + 1)  # old method
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
                if not team["name"] is "":  # if there wasn't a 404 error, check if there is existing data on team
                    matches = cursor.execute(CHECK_TEAM_TABLE.format("Teams", team_id))
                    if matches.fetchone() is None:  # if there are no duplicates, add the team to team table
                        cursor.execute(ADD_TO_TEAM_TABLE.format("Teams", team["name"], team_id))
                for index, swimmer in enumerate(team["roster"]):
                    print(swimmer[0] + " " + swimmer[1])  # for each swimmer on the team

                    # enumerate this loop to have an index for the loading bar
                    percent_of_team = float(index) / float(len(team["roster"]))
                    show_loading_bar(percent + (percent_of_team / float(len(teams_to_pull))))

                    # add the swimmer to the Swimmers table, if they aren't there already
                    matches = cursor.execute(CHECK_SWIMMER_TABLE.format("Swimmers", swimmer[1]))
                    if matches.fetchone() is None:
                        cursor.execute(ADD_TO_SWIMMER_TABLE.format("Swimmers", sqlsafe(swimmer[0]), gender, swimmer[1], team_id))
                    # Add all of this swimmer's swim data for this season to the swims table, for the events requested
                    for event in events_to_pull:  # pull swim data for requested events
                        print(swimmer[1] + " " + event)
                        swims = request_swimmer(swimmer[1], event, search_start_timestamp, search_end_timestamp)
                        sys.stdout.flush()
                        # Add swims to Swims table
                        for swim in swims:
                            command = INSERT_SWIM_COMMAND.format(swimmer[1], team_id, swim[1], 0, swim[2], gender, event, swim[0], 0, snapshot_id)
                            cursor.execute(command)

                # Retrieve relay swim data and data on meets that team team_id competed in
                relay_swims, meets = get_relay_swim_data(team_id, gender, season_string, relays_to_pull)

                # Add relay swim data to database swims table
                for relay_swim in relay_swims:
                    relay_command = INSERT_SWIM_COMMAND.format(relay_swim[0],relay_swim[1],relay_swim[2],0,
                                                               relay_swim[4], relay_swim[5], relay_swim[6],
                                                               relay_swim[7], 0, snapshot_id)
                    cursor.execute(relay_command)

                # Add meet data to database meets table
                # NOTE: Meets table still hasn't been pulled/created yet, if get_swim_data fails try commenting out this
                #for meet in meets:
                #    matches = cursor.execute(CHECK_MEET_TABLE.format(meet))
                #    if matches.fetchone() is None:
                #        meet_command = INSERT_MEET_COMMAND.format(meet, meets[meet]["meet_name"],
                #                                                  meets[meet]["meet_date"],
                #                                                  meets[meet]["submitted"])
                #        cursor.execute(meet_command)

                # print the loading bar
                team_counter += 1
                percent = float(team_counter) / float(len(teams_to_pull))
                show_loading_bar(percent)

        connection.commit()

    ####################################################################################################################
    # REMAINDER OF CODE HERE ISN'T USED FOR OUR PURPOSES                                                               #
    # this code doesn't work for relay swims                                                                           #
    ####################################################################################################################

    get_event_times = "SELECT time FROM Swims WHERE event='{}{}' AND date>{} AND date<{}"
    update_with_scaled = "UPDATE Swims SET scaled={} WHERE event='{}{}' AND date>{} AND date<{} AND time={}"
    # fill out the scaled column
    print("Scaling times")
    # convert each swim to a season z-score
    for simple_year in range(year_start, year_end):
        season_start_timestamp = convert_to_time(int(simple_year), SEASON_LINE_MONTH, SEASON_LINE_DAY)
        season_end_timestamp = convert_to_time(int(simple_year) + 1, SEASON_LINE_MONTH, SEASON_LINE_DAY)
        for event in events_to_pull:
            for gender in genders_to_pull:
                # calculate average times for each event by gender
                cursor.execute(get_event_times.format(gender, event, season_start_timestamp, season_end_timestamp))
                times = [x[0] for x in cursor.fetchall()]
                try:
                    average = sum(times) / len(times)
                except ZeroDivisionError as e:
                    print("No data was available on event {}".format(event))
                    continue
                print("average for {}{} in {}: {}".format(gender, event, simple_year, average))
                # calculate z-score of times scored for this event-gender pairing
                sd = (sum([(x - average)**2 for x in times]) / len(times)) ** .5  # standard deviation
                update_list = [(x, (x - average) / sd) for x in times]
                for update in update_list:
                    command = update_with_scaled.format(update[1], gender, event, season_start_timestamp,
                                                        season_end_timestamp, update[0])
                    cursor.execute(command)
    connection.commit()
    print("scaled")

    print("\nFinding taper swims")
    for simple_year in range(year_start, year_end):
        season_start_timestamp = convert_to_time(int(simple_year), SEASON_LINE_MONTH, SEASON_LINE_DAY)
        season_end_timestamp = convert_to_time(int(simple_year) + 1, SEASON_LINE_MONTH, SEASON_LINE_DAY)
        print("Season {}-{}".format(simple_year, simple_year + 1))
        print("From timestamp {} to {}".format(season_start_timestamp, season_end_timestamp))
        for team_id in teams_to_pull:
            # get a list of all the days this team swam
            cursor.execute("SELECT date FROM Swims WHERE team={} AND date>{} AND date<{}".format(team_id,
                                                                                                 season_start_timestamp,
                                                                                                 season_end_timestamp))
            dates = cursor.fetchall()
            dates = list(set(dates))  # this removes duplicates, which there are many
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
                # Brad's interpretation of this:
                # If a swim was better than team average, give taper of 1, otherwise set taper to 2
                if date[0] < average_score:
                    cursor.execute("UPDATE Swims SET taper=1 WHERE team={} AND date={}".format(team_id, date[1]))
                else:
                    cursor.execute("UPDATE Swims SET taper=2 WHERE team={} AND date={}".format(team_id, date[1]))

    print("Finding outliers")
    cursor.execute("UPDATE Swims SET taper=3 WHERE scaled>3")  # a lazy solution. I'm tired << let's fix that

    connection.commit()
    connection.close()


# This function is meant for letting you choose the inputs that are used when calling get_swim_data. Feel free to mess
# with it as you like
def inputs_for_swim_data_search(all_default=False):
    """
        allows you to input values for get_swim_data as you like. if all_default is True you can input things manually
        upon calling the function. if it is False then it will just use default values listed in constants.py
    """
    if all_default == True:
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
    inputs_for_swim_data_search(True)


main()
