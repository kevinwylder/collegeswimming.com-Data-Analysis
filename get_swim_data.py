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


def requestSwimmer(swimmerId, event, searchStartTimestamp, searchEndTimestamp):
    """
    Input a swimmerID and event.
    Output list of tuples containing event swim's in a tuple containing the date
    they participated in the event and the time they achieved while competing.
    tuple format is (date, swimtime)
    """
    swimmerData = []
    swimmerEvents = []
    url = SWIMMER_URL.format(swimmerId)
    print(url)
    try:# to open a url for that swimmer and read their data
        page = urllib.request.urlopen(url)
        source = page.read()
    except urllib.request.HTTPError as e:
        print(e) # otherwise print out the error and return empty tuple
        return ([],"")
    soup = BeautifulSoup(source, 'html.parser')
    selection = soup.find("select", class_="form-control input-sm js-event-id-selector")
    if selection:
        for eventOption in selection.find_all("option", class_="event"):
            swimmerEvents.append(eventOption["value"])

    # If the event you want data on is contained within the list of events they have data for that swimmer on, then add that data to swimmerData
    if event in swimmerEvents:
        url = SWIMMER_EVENT_URL.format(swimmerId, event)
        print(url)
        page = urllib.request.urlopen(url)
        source = page.read()
        eventHistory = json.loads(source)
        for swim in eventHistory:
            # convert the date string to epoch
            splitDate = swim["dateofswim"].split("-")
            date = convertToTime(int(splitDate[0]), int(splitDate[1]), int(splitDate[2]))
            if date > searchStartTimestamp and date < searchEndTimestamp:  # defined below the timestamp function and updated every year loop
                swimTuple = (date, swim["time"])
                swimmerData.append(swimTuple)
    return swimmerData

def getRoster(teamId, season, gender):
    """
        Input: a teamId, season, and gender used to uniquely identify a team
        Output: List of tuples containing swimmer names and IDs
    """
    team = {}
    'gets a list of (Name, swimmerId) tuples and the team name for a given teamId'
    url = ROSTER_URL.format(teamId, season, gender)
    print(url)
    try:
        page = urllib.request.urlopen(url)
        source = page.read()
    except urllib.request.HTTPError as e:
        print(e) # otherwise print out the error and return empty tuple
        return ([],"")
    soup = BeautifulSoup(source, 'html.parser')
    team["name"] = soup.find("h1", class_="c-toolbar__title").text

    tableBody = soup.find("table", class_="c-table-clean c-table-clean--middle c-table-clean--fixed table table-hover").tbody
    team["roster"] = []
    for tableRow in tableBody.find_all("tr"):
        swimmerId = tableRow.td.a["href"].split("/")[-1]
        swimmerName = normalizeName(str(tableRow.td.strong.text))
        team["roster"].append( (swimmerName, swimmerId) )
    return team

def getSwimData(teamsToPull, gendersToPull,
                yearStart, yearEnd,
                eventsToPull = DEFAULT_EVENTS_TO_PULL,
                databaseFileName = DATABASE_FILE_NAME,):
    # open the sqlite database
    for team in range(len(teamsToPull)):
        teamsToPull[team] = TEAM_DICT[teamsToPull[team]]
    
    connection = sqlite3.connect(databaseFileName)
    cursor = connection.cursor()

    # add information about this snapshot to the Snapshots table (and create it if it doesn't exist)
    cursor.execute(CREATE_SNAPSHOT_TABLE_COMMAND)
    snapshotId = random.randint(0, 4294967295) # what are the odds? 100% I'm a lazy programmer
    dateRangeString = "{0}.{1}.{2}-{3}.{1}.{2}".format(yearStart, SEASON_LINE_MONTH, SEASON_LINE_DAY, yearEnd)#creates a string representing a range of dates equal to yearEnd-yearStart years
    teamsString = ",".join(str(team) for team in teamsToPull)
    eventsString = ",".join(eventsToPull)
    cursor.execute(INSERT_SNAPSHOT_COMMAND.format(snapshotId, dateRangeString, teamsString, eventsString))

    # ensure the existence of each event table and the Teams/Swimmers tables
    cursor.execute(CREATE_SWIMS_TABLE)
    cursor.execute(CREATE_NAME_TABLE.format("Swimmers"))
    cursor.execute(CREATE_NAME_TABLE.format("Teams"))
    
    
    # retrieve and add the times to the database
    for simpleYear in range(yearStart, yearEnd):   # for each competition year
        seasonString = str(simpleYear) + "-" + str(simpleYear + 1)
        print("Collecting Season {}".format(seasonString))
        searchStartTimestamp = convertToTime(int(simpleYear), SEASON_LINE_MONTH, SEASON_LINE_DAY)
        searchEndTimestamp = convertToTime(int(simpleYear)+1, SEASON_LINE_MONTH, SEASON_LINE_DAY)
        teamCounter = 0
        percent = 0
        for teamId in teamsToPull:   # for each team
            for gender in gendersToPull:  # for each gender
                # pull the roster for this season and gender
                team = getRoster(teamId, seasonString, gender)
                print (team)
                # add team to the Teams table
                if not team["name"] is "":  # if there wasn't a 404 error
                    matches = cursor.execute(CHECK_NAME_TABLE.format("Teams", teamId))
                    if matches.fetchone() is None:  # if there are no duplicates
                        cursor.execute(ADD_TO_NAME_TABLE.format("Teams", team["name"], teamId))
                for index, swimmer in enumerate(team["roster"]):
                    print (swimmer[0] + " " + swimmer[1])# for each swimmer on the team
                    # enumerate this loop to have an index for the loading bar
                    percentOfTeam = float(index) / float(len(team["roster"]))
                    showLoadingBar(percent + (percentOfTeam / float(len(teamsToPull))))
                    # add the swimmer to the Names table
                    matches = cursor.execute(CHECK_NAME_TABLE.format("Swimmers", swimmer[1]))
                    if matches.fetchone() is None:
                        cursor.execute(ADD_TO_NAME_TABLE.format("Swimmers", sqlsafe(swimmer[0]), swimmer[1]))
                    for event in eventsToPull:   # for each of this swimmer's event we're searching
                        print (swimmer[1] + " " + event)
                        swims = requestSwimmer(swimmer[1], event, searchStartTimestamp, searchEndTimestamp)
                        sys.stdout.flush()
                        for swim in swims:   # for each qualified race
                            # add this race to the database
                            command = INSERT_SWIM_COMMAND.format(swimmer[1], teamId, swim[1], 0, gender, event, swim[0], 0, snapshotId)
                            cursor.execute(command)
                # print the loading bar
                teamCounter += 1
                percent = float(teamCounter) / float(len(teamsToPull))
                showLoadingBar(percent)
        connection.commit()

    getEventTimes = "select time from Swims where event='{}{}' and date>{} and date<{}"#I can update this a bit (See notes)
    updateWithScaled = "update Swims set scaled={} where event='{}{}' and date>{} and date<{} and time={}"
    # fill out the scaled column
    print ("Scaling times")
    # convert each swim to a season z-score
    for simpleYear in range(yearStart, yearEnd):   # for each competition year
        seasonStartTimestamp = convertToTime(int(simpleYear), SEASON_LINE_MONTH, SEASON_LINE_DAY)
        seasonEndTimestamp = convertToTime(int(simpleYear)+1, SEASON_LINE_MONTH, SEASON_LINE_DAY)
        for event in eventsToPull:
            for gender in gendersToPull:
                cursor.execute(getEventTimes.format(gender, event, seasonStartTimestamp, seasonEndTimestamp))
                times = [x[0] for x in cursor.fetchall()]
                try:
                    average = sum(times) / len(times)
                except ZeroDivisionError as e:
                    print("No data was available on event {}".format(event))
                    continue
                print ("average for {}{} in {}: {}".format(gender, event, simpleYear, average))
                sd = (sum([(x - average)**2 for x in times]) / len(times)) ** .5 # sqrt(sum of rediduals squared normalized to n)
                updateList = [(x, (x - average) / sd) for x in times]
                for update in updateList:
                    command = updateWithScaled.format(update[1], gender, event, seasonStartTimestamp, seasonEndTimestamp, update[0])
                    cursor.execute(command)
    connection.commit()
    print ("scaled")


    print ("")
    print ("Finding taper swims")
    for simpleYear in range(yearStart, yearEnd):
        seasonStartTimestamp = convertToTime(int(simpleYear), SEASON_LINE_MONTH, SEASON_LINE_DAY)
        seasonEndTimestamp = convertToTime(int(simpleYear)+1, SEASON_LINE_MONTH, SEASON_LINE_DAY)
        print ("Season {}-{}".format(simpleYear, simpleYear + 1))
        print ("From timestamp {} to {}".format(seasonStartTimestamp, seasonEndTimestamp))
        for teamId in teamsToPull:
            # get a list of all the days this team swam
            cursor.execute("select date from Swims where team={} and date>{} and date<{}".format(teamId, seasonStartTimestamp, seasonEndTimestamp))
            dates = cursor.fetchall()
            dates = list(set(dates)) # this removes duplicates, which there are many
            meetScores = []             # populate this with
            averageScore = 0
            for date in dates:
                # first check if only one swimmer swam. this is indicative of a glitch where I
                # cannot isolate which roster a swimmer is in if they switched team.
                cursor.execute("select count(*) from Swims where team={} and date={}".format(teamId, date[0]))
                if cursor.fetchone()[0] != 7:
                    # get the average scaled time for this day of swimming and add it to the list
                    cursor.execute("select avg(scaled) from Swims where team={} and date={}".format(teamId, date[0]))
                    meetTuple = (cursor.fetchone()[0], date[0])
                    averageScore += meetTuple[0]
                    meetScores.append(meetTuple)
            averageScore /= len(dates)
            for date in meetScores:
                # a taper swim is a swim at a meet with a below average z-score for that season
                # this can be assumed because, given that a team has dual meets and taper meets
                # online, there will be a two-node normal distribution. the lower node contains
                # taper swims. we'll now update them in the database
                if date[0] < averageScore:
                    cursor.execute("update Swims set taper=1 where team={} and date={}".format(teamId, date[1]))
                else:
                    cursor.execute("update Swims set taper=2 where team={} and date={}".format(teamId, date[1]))

    print ("Finding outliers")
    cursor.execute("update Swims set taper=3 where scaled>3")    # a lazy solution. I'm tired


    connection.commit()
    connection.close()

#Not sure how to credit this now.
#print ("Check {} for results".format(databaseFileName))
#print ("Written by Kevin Wylder")
#print ("contact at wylderkevin@gmail.com")

def inputsForSwimDataSearch(allDefault = False):
    """
        allows you to input test values for
        """
    if (allDefault == True):
        eventsToPull = DEFAULT_EVENTS_TO_PULL
        gendersToPull = DEFAULT_GENDER
        teamsToPull = DEFAULT_TEAMS_TO_PULL
        yearStart = DEFAULT_YEAR_START
        yearEnd = DEFAULT_YEAR_END
        databaseFileName = DATABASE_FILE_NAME
    else:
        databaseFileName = input("Use default database file? Y/N ")
        if (databaseFileName == "Y"):
            databaseFileName = DATABASE_FILE_NAME
        else:
            databaseFileName = input("Type database file name here: ")
        #eventsToPull = input("Which events would you like to pull information on? Separate with spaces please ").split()
        teamsToPull = []
        tempVal = input("Input colleges whose teams you would like to pull one at a time. Hit \"return\" after each entry.\n1. ")
        while (tempVal != ("done" or "Done")):
            teamsToPull.append(tempVal)
            tempVal = input("\n{}. ".format(len(teamsToPull)+1))
        gendersToPull = input("M, F, or M F? ").split()
        yearStart = eval(input("Input start year"))
        yearEnd = eval(input("Input end year"))
        eventsToPull = DEFAULT_EVENTS_TO_PULL
    return getSwimData(teamsToPull, gendersToPull, yearStart, yearEnd, eventsToPull, databaseFileName)

def main():
    inputsForSwimDataSearch(False)
main()
