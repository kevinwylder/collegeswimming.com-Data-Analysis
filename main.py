import urllib.request
import json
import sqlite3
import random
import sys
import parameters
from bs4 import BeautifulSoup
#import re
#import string

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# College Swimming Spring Break Project 2015                                Kevin Wylder #
#                                                                                        #
# This file builds a database from data collected off collegeswimming.com                #
# for more detail on the structure of the database, the global variables in this file,   #
# or the collegeswimming.com website structure, see the README                           #
#                                                                                        #
# From here on out, 90 character width isn't guarenteed                                   #
 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# setup search and output parameters
parameters = parameters.Parameters()
databaseFileName = parameters.databaseFileName
eventsToPull = parameters.eventsToPull
gendersToPull = parameters.gendersToPull
teamsToPull = parameters.teamsToPull
yearStart = parameters.yearStart
yearEnd = parameters.yearEnd
seasonLineMonth = parameters.seasonLineMonth
seasonLineDay = parameters.seasonLineDay

swimmerUrl = "https://www.collegeswimming.com/swimmer/{}"
swimmerEventUrl = "https://www.collegeswimming.com/swimmer/{}/times/byeventid/{}"
rosterUrl = "https://www.collegeswimming.com/team/{}/roster?season={}&gender={}"

createSwimsTable = "create table if not exists Swims (swimmer INTEGER, team INTEGER, time REAL, scaled REAL, event TEXT, date INTEGER, taper INTEGER, snapshot INTEGER);"
insertSwimCommand = "insert into Swims values({}, {}, {}, {}, '{}{}', {}, {}, {});"
createSnapshotTableCommand = "create table if not exists Snapshots (snapshot INTEGER, date TEXT, teams TEXT, events TEXT);"
insertSnapshotCommand = "insert into Snapshots values({}, '{}', '{}', '{}');"
createNameTable = "create table if not exists {} (name TEXT, id INTEGER);"
checkNameTable = 'select id from {} where id={} limit 1;'
addToNameTable = "insert into {} values('{}', {});"

searchStartTimestamp = 0
searchEndTimestamp = 0

def normalizeName(name):
    nameParts = name.split()
    name = " ".join([part.lower().capitalize() for part in nameParts])
    n = name.find("'")
    if n > -1:
        name = name[:n+1] + name[n+1:].capitalize()
    return name

def sqlsafe(name):
    n = name.find("'")
    if n > -1:
        name = name[:n+1] + "'" + name[n+1:]
    return name

def showLoadingBar(percent):
    chars = int(percent * 50)
    sys.stdout.write(("#" * chars) + (" " * (50 - chars)) + " {:10.2f}%\r".format(100 * percent))
    sys.stdout.flush()

def requestSwimmer(swimmerId, event):

    'returns this event\'s swims for the swimmerId in the format (date, time)'
    swimmerData = []
    swimmerEvents = []
    url = swimmerUrl.format(swimmerId)
    try:
        page = urllib.request.urlopen(url)
        source = page.read()
    except urllib.request.HTTPError as e:
        print(e)
        return ([],"")
    soup = BeautifulSoup(source, 'html.parser')
    selection = soup.find("select", class_="form-control input-sm js-event-id-selector")
    if selection:
        for option in selection.find_all("option", class_="event"):
            thisEvent = option["value"]
            swimmerEvents.append(thisEvent)

    if event in swimmerEvents:
        url = swimmerEventUrl.format(swimmerId, event)
        page = urllib.request.urlopen(url)
        source = page.read()
        eventHistory = json.loads(source)
        for swim in eventHistory:
            # convert the date string to epoch
            splitDate = swim["dateofswim"].split("-")
            date = parameters.convertToTimestamp(splitDate[0], splitDate[1], splitDate[2])
            if date > searchStartTimestamp and date < searchEndTimestamp:  # defined below the timestamp function and updated every year loop
                swimTuple = (date, swim["time"])
                swimmerData.append(swimTuple)
    return swimmerData

def getRoster(teamId, season, gender):
    team = {}
    'gets a list of (Name, swimmerId) tuples and the team name for a given teamId'
    url = rosterUrl.format(teamId, season, gender)
    try:
        page = urllib.request.urlopen(url)
        source = page.read()
    except urllib.request.HTTPError as e:
        print(e)
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


##############################
# !!! script starts here !!! #
##############################

# open the sqlite database
connection = sqlite3.connect(databaseFileName)
cursor = connection.cursor()

# add information about this snapshot to the Snapshots table (and create it if it doesn't exist)
cursor.execute(createSnapshotTableCommand);
snapshotId = random.randint(0, 4294967295) # what are the odds? 100% I'm a lazy programmer
dateRangeString = "{0}.{1}.{2}-{3}.{1}.{2}".format(yearStart, seasonLineMonth, seasonLineDay, yearEnd)
teamsString = ",".join(str(team) for team in teamsToPull)
eventsString = ",".join(eventsToPull)
cursor.execute(insertSnapshotCommand.format(snapshotId, dateRangeString, teamsString, eventsString))

# ensure the existence of each event table and the Teams/Swimmers tables
cursor.execute(createSwimsTable)
cursor.execute(createNameTable.format("Swimmers"))
cursor.execute(createNameTable.format("Teams"))

# retrieve and add the times to the database
for simpleYear in range(yearStart, yearEnd):   # for each competition year
    seasonString = str(simpleYear) + "-" + str(simpleYear + 1)
    print("Collecting Season {}".format(seasonString))
    searchStartTimestamp = parameters.convertToTimestamp(simpleYear, seasonLineMonth, seasonLineDay)
    searchEndTimestamp = parameters.convertToTimestamp(simpleYear + 1, seasonLineMonth, seasonLineDay)
    teamCounter = 0
    percent = 0
    for teamId in teamsToPull:   # for each team
        for gender in gendersToPull:  # for each gender
            # pull the roster for this season and gender
            team = getRoster(teamId, seasonString, gender)
            print (team)
            # add team to the Teams table
            if not team["name"] is "":  # if there wasn't a 404 error
                matches = cursor.execute(checkNameTable.format("Teams", teamId))
                if matches.fetchone() is None:  # if there are no duplicates
                    cursor.execute(addToNameTable.format("Teams", team["name"], teamId))
            for index, swimmer in enumerate(team["roster"]):
                print (swimmer[0] + " " + swimmer[1])# for each swimmer on the team
                # enumerate this loop to have an index for the loading bar
                percentOfTeam = float(index) / float(len(team["roster"]))
                showLoadingBar(percent + (percentOfTeam / float(len(teamsToPull) * 2)))
                # add the swimmer to the Names table
                matches = cursor.execute(checkNameTable.format("Swimmers", swimmer[1]))
                if matches.fetchone() is None:
                    cursor.execute(addToNameTable.format("Swimmers", sqlsafe(swimmer[0]), swimmer[1]))
                for event in eventsToPull:   # for each of this swimmer's event we're searching
                    print (swimmer[1] + " " + event)
                    swims = requestSwimmer(swimmer[1], event)
                    for swim in swims:   # for each qualified race
                        # add this race to the database
                        print (swim)
                        command = insertSwimCommand.format(swimmer[1], teamId, swim[1], 0, gender, event, swim[0], 0, snapshotId)
                        cursor.execute(command)
            # print the loading bar
            teamCounter += 1
            percent = float(teamCounter) / float(len(teamsToPull) * 2)
            showLoadingBar(percent)
    # finish the loading bar
    print ("#"*50)
    print ("")
    connection.commit()

getEventTimes = "select time from Swims where event='{}{}' and date>{} and date<{}"
updateWithScaled = "update Swims set scaled={} where event='{}{}' and date>{} and date<{} and time={}"
# fill out the scaled column
print ("Scaling times")
# convert each swim to a season z-score
for simpleYear in range(yearStart, yearEnd):   # for each competition year
    seasonStartTimestamp = parameters.convertToTimestamp(simpleYear, seasonLineMonth, seasonLineDay)
    seasonEndTimestamp = parameters.convertToTimestamp(simpleYear + 1, seasonLineMonth, seasonLineDay)
    for event in eventsToPull:
        for gender in gendersToPull: # for each event
            cursor.execute(getEventTimes.format(gender, event, seasonStartTimestamp, seasonEndTimestamp))
            times = [x[0] for x in cursor.fetchall()]
            average = sum(times) / len(times)
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
    seasonStartTimestamp = parameters.convertToTimestamp(simpleYear, seasonLineMonth, seasonLineDay)
    seasonEndTimestamp = parameters.convertToTimestamp(simpleYear + 1, seasonLineMonth, seasonLineDay)
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
print ("")
print ("")
print ("###################")
print ("# script complete #")
print ("###################")
print ("Check {} for results".format(databaseFileName))
print ("Written by Kevin Wylder")
print ("contact at wylderkevin@gmail.com")
