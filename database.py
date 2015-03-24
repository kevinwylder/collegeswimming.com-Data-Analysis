import urllib2
import json
import sqlite3
import datetime
import random

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# College Swimming Spring Break Project 2015                                Kevin Wylder #
#                                                                                        #
# This file builds a database from data collected off collegeswimming.com                #
# for more detail on the structure of the database, the global variables in this file,   #
# or the collegeswimming.com website structure, see the README                           #
#                                                                                        #
# From here on out, 90 character width isn't guarenteed                                   #
 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# search and output parameters
databaseFileName = "collegeswimming.db"
eventsToPull = ["150Y", "4100Y", "1100Y"]
gendersToPull = ["M"]
teamsToPull = [121]
yearStart = 2010
yearEnd = 2015
seasonLineMonth = 9
seasonLineDay = 15

swimmerEventUrl = "http://www.collegeswimming.com/swimmer/{}/times/byeventid/{}"
teamRosterUrl = "http://www.collegeswimming.com/team/{}/mod/teamroster?season={}&gender={}"

addTableCommand = "create table if not exists {}{} (name INTEGER, team INTEGER, time REAL, date INTEGER, taper INTEGER, snapshot INTEGER);"
insertTimeCommand = "insert into {}{} values({}, {}, {}, {}, {}, {});"
createSnapshotTableCommand = "create table if not exists Snapshots (snapshot INTEGER, date TEXT, teams TEXT, events TEXT);"
insertSnapshotCommand = "insert into Snapshots values({}, '{}', '{}', '{}');"
createNameTable = "create table if not exists {} (name TEXT, id INTEGER);"
checkNameTable = "select id from {} where id={} limit 1;"
addToNameTable = "insert into {} values('{}', {});"

def convertToTimestamp(year, month, day):
	'converts a given month day and year into a timestamp. Why is this so hard?'
	return (datetime.datetime(int(year), int(month), int(day)) - datetime.datetime(1970,1,1)).total_seconds()

searchStartTimestamp = 0
searchEndTimestamp = 0

def requestSwimmer(swimmerId, event):
	'returns this event\'s swims for the swimmerId in the format (date, time)'
	swimmerData = []
	url = swimmerEventUrl.format(swimmerId, event)
	page = urllib2.urlopen(url)
	source = page.read()
	eventHistory = json.loads(source)
	for swim in eventHistory:
		# convert the date string to epoch
		splitDate = swim["dateofswim"].split("-")		
		date = convertToTimestamp(splitDate[0], splitDate[1], splitDate[2])
		if date > searchStartTimestamp and date < searchEndTimestamp:  # defined below the timestamp function and updated every year loop
			swimTuple = (date, swim["time"])
			swimmerData.append(swimTuple)
	return swimmerData

def requestTeamRoster(teamId, season, gender):
	'gets a list of (Name, swimmerId) tuples and the team name for a given teamId'
	teamRoster = []
	url = teamRosterUrl.format(teamId, season, gender)
	try:
		page = urllib2.urlopen(url)
		source = page.read()
	except urllib2.HTTPError:
		return ([],"")
	# our own form of parsing. better than using an external library
	rows = source.split("<td><a href=\"/swimmer/")
	for row in rows:
		if "</a></td>" in row:	# having this string ensures good data
			swimmerInfo = row.split("</a></td>")[0]
			swimmerIdSplit = swimmerInfo.split("\">")
			# sanitize the name
			swimmerIdSplit[1] = swimmerIdSplit[1].translate(None, "';\".")
			nameSplit = swimmerIdSplit[1].split(", ")
			teammate = (nameSplit[1] + " " + nameSplit[0], swimmerIdSplit[0])
			teamRoster.append(teammate)
	teamName = source.split("<h1 class=\"team-name\">")[1].split("</h1>")[0]
	return (teamRoster, teamName)

	
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
for gender in gendersToPull:
	for event in eventsToPull:
		cursor.execute(addTableCommand.format(gender, event))
cursor.execute(createNameTable.format("Swimmers"))
cursor.execute(createNameTable.format("Teams"))

raceCounter = 0;
# retrieve and add the times to the database
for simpleYear in range(yearStart, yearEnd):   # for each competition year
	seasonString = str(simpleYear) + "-" + str(simpleYear + 1)
	print "{0:08d} times".format(raceCounter)
	print "Collecting Season {}".format(seasonString)
	searchStartTimestamp = convertToTimestamp(simpleYear, seasonLineMonth, seasonLineDay)
	searchEndTimestamp = convertToTimestamp(simpleYear + 1, seasonLineMonth, seasonLineDay)
	for teamId in teamsToPull:   # for each team
		for gender in gendersToPull:  # for each gender
			# pull the roster for this season and gender
			teamInfo = requestTeamRoster(teamId, seasonString, gender)
			
			# add team to the Teams table
			if not teamInfo[1] is "":  # if there wasn't a 404 error
				matches = cursor.execute(checkNameTable.format("Teams", teamId))
				if matches.fetchone() is None:  # if there are no duplicates
					cursor.execute(addToNameTable.format("Teams", teamInfo[1], teamId))
			
			for swimmer in teamInfo[0]:   # for each swimmer on the team
			
				# add the swimmer to the Names table
				matches = cursor.execute(checkNameTable.format("Swimmers", swimmer[1]))
				if matches.fetchone() is None:
					cursor.execute(addToNameTable.format("Swimmers", swimmer[0], swimmer[1]))
				
				for event in eventsToPull:   # for each event we're searching
					swims = requestSwimmer(swimmer[1], event)
					raceCounter += len(swims)
					for swim in swims:   # for each qualified race
						# add this race to the database
						command = insertTimeCommand.format(gender, event, swimmer[1], teamId, swim[1], swim[0], 0, snapshotId)
						cursor.execute(command)

# save the database
connection.commit()
connection.close()
		