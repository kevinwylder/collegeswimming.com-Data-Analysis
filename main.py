import urllib2
import json
import sqlite3
import datetime
import random
import subprocess
import sys

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
eventsToPull = ["150Y", "4100Y", "1100Y", "2100Y", "3100Y", "11000Y", "1500Y", "1200Y"]
gendersToPull = ["M", "F"]
teamsToPull = [51, 107, 116, 121, 131, 154, 155, 188, 194, 261, 362, 337, 384, 385, 390, 417, 447, 496, 497, 499, 517, 528, 542, 639]
yearStart = 2010
yearEnd = 2015
seasonLineMonth = 9
seasonLineDay = 15

swimmerEventUrl = "http://www.collegeswimming.com/swimmer/{}/times/byeventid/{}"
teamRosterUrl = "http://www.collegeswimming.com/team/{}/mod/teamroster?season={}&gender={}"

createSwimsTable = "create table if not exists Swims (swimmer INTEGER, team INTEGER, time REAL, scaled REAL, event TEXT, date INTEGER, taper INTEGER, snapshot INTEGER);"
insertSwimCommand = "insert into Swims values({}, {}, {}, {}, '{}{}', {}, {}, {});"
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

def scaleList(list):
	"return a list of z-scores of the input"

def showLoadingBar(percent):
	chars = int(percent * 50)
	sys.stdout.write(("#" * chars) + (" " * (50 - chars)) + " {:10.2f}%\r".format(100 * percent))
	sys.stdout.flush()

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
			if "," in swimmerIdSplit[1]:
				nameSplit = swimmerIdSplit[1].split(", ")
				teammate = (nameSplit[1] + " " + nameSplit[0], swimmerIdSplit[0])
				teamRoster.append(teammate)
			else:
				teammate = (swimmerIdSplit[1], swimmerIdSplit[0])
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
# cursor.execute(createSnapshotTableCommand);
# snapshotId = random.randint(0, 4294967295) # what are the odds? 100% I'm a lazy programmer
# dateRangeString = "{0}.{1}.{2}-{3}.{1}.{2}".format(yearStart, seasonLineMonth, seasonLineDay, yearEnd)
# teamsString = ",".join(str(team) for team in teamsToPull)
# eventsString = ",".join(eventsToPull)
# cursor.execute(insertSnapshotCommand.format(snapshotId, dateRangeString, teamsString, eventsString))
# 
# # ensure the existence of each event table and the Teams/Swimmers tables
# cursor.execute(createSwimsTable)
# cursor.execute(createNameTable.format("Swimmers"))
# cursor.execute(createNameTable.format("Teams"))
# 
# # retrieve and add the times to the database
# for simpleYear in range(yearStart, yearEnd):   # for each competition year
# 	seasonString = str(simpleYear) + "-" + str(simpleYear + 1)
# 	print "Collecting Season {}".format(seasonString)
# 	searchStartTimestamp = convertToTimestamp(simpleYear, seasonLineMonth, seasonLineDay)
# 	searchEndTimestamp = convertToTimestamp(simpleYear + 1, seasonLineMonth, seasonLineDay)
# 	teamCounter = 0
# 	percent = 0
# 	for teamId in teamsToPull:   # for each team
# 		for gender in gendersToPull:  # for each gender
# 			# pull the roster for this season and gender
# 			teamInfo = requestTeamRoster(teamId, seasonString, gender)
# 			# add team to the Teams table
# 			if not teamInfo[1] is "":  # if there wasn't a 404 error
# 				matches = cursor.execute(checkNameTable.format("Teams", teamId))
# 				if matches.fetchone() is None:  # if there are no duplicates
# 					cursor.execute(addToNameTable.format("Teams", teamInfo[1], teamId))
# 			for index, swimmer in enumerate(teamInfo[0]):   # for each swimmer on the team
# 				# enumerate this loop to have an index for the loading bar
# 				percentOfTeam = float(index) / float(len(teamInfo[0]))
# 				showLoadingBar(percent + (percentOfTeam / float(len(teamsToPull) * 2)))
# 				# add the swimmer to the Names table
# 				matches = cursor.execute(checkNameTable.format("Swimmers", swimmer[1]))
# 				if matches.fetchone() is None:
# 					cursor.execute(addToNameTable.format("Swimmers", swimmer[0], swimmer[1]))
# 				for event in eventsToPull:   # for each of this swimmer's event we're searching
# 					swims = requestSwimmer(swimmer[1], event)
# 					for swim in swims:   # for each qualified race
# 						# add this race to the database
# 						command = insertSwimCommand.format(swimmer[1], teamId, swim[1], 0, gender, event, swim[0], 0, snapshotId)
# 						cursor.execute(command)
# 			# print the loading bar
# 			teamCounter += 1
# 			percent = float(teamCounter) / float(len(teamsToPull) * 2)
# 			showLoadingBar(percent)
# 	# finish the loading bar
# 	print "#" * 50
# 	print ""
# 	connection.commit()
# 
# # save the database
# connection.commit()
# 
# getEventTimes = "select time from Swims where event='{}{}' and date>{} and date<{}"
# updateWithScaled = "update Swims set scaled={} where event='{}{}' and date>{} and date<{} and time={}"
# # fill out the scaled column
# print "Scaling times"
# # convert each swim to a season z-score
# for simpleYear in range(yearStart, yearEnd):   # for each competition year
# 	seasonStartTimestamp = convertToTimestamp(simpleYear, seasonLineMonth, seasonLineDay)
# 	seasonEndTimestamp = convertToTimestamp(simpleYear + 1, seasonLineMonth, seasonLineDay)
# 	for event in eventsToPull:
# 		for gender in gendersToPull: # for each event
# 			cursor.execute(getEventTimes.format(gender, event, seasonStartTimestamp, seasonEndTimestamp))
# 			times = [x[0] for x in cursor.fetchall()]
# 			average = sum(times) / len(times)
# 			print "average for {}{} in {}: {}".format(gender, event, simpleYear, average)
# 			sd = (sum([(x - average)**2 for x in times]) / len(times)) ** .5 # sqrt(sum of rediduals squared normalized to n)
# 			updateList = [(x, (x - average) / sd) for x in times]
# 			for update in updateList:
# 				command = updateWithScaled.format(update[1], gender, event, seasonStartTimestamp, seasonEndTimestamp, update[0])
# 				cursor.execute(command)
# connection.commit()

print "scaled"
print ""
print "Finding taper swims"
for simpleYear in range(yearStart, yearEnd):
	seasonStartTimestamp = convertToTimestamp(simpleYear, seasonLineMonth, seasonLineDay)
	seasonEndTimestamp = convertToTimestamp(simpleYear + 1, seasonLineMonth, seasonLineDay)
	print "Season {}-{}".format(simpleYear, simpleYear + 1)
	print "From {} to {}".format(seasonStartTimestamp, seasonEndTimestamp)
	for teamId in [121]: #teamsToPull: Only test UCSD to see what a taper swim looks like
		# get the average z-score of a given team's swim
		cursor.execute("select scaled from Swims where team={} and date>{} and date<{}".format(teamId, seasonStartTimestamp, seasonEndTimestamp))
		averageSeason = cursor.fetchone()[0]
		# get a list of all the days this team swam
		cursor.execute("select date from Swims where team={} and date>{} and date<{}".format(teamId, seasonStartTimestamp, seasonEndTimestamp))
		dates = cursor.fetchall()
		dates = list(set(dates)) # this removes duplicates, which there are many
		meetScores = []			 # populate this with
		for date in dates:
			# did this day have an unusually low average z score?
			cursor.execute("select avg(scaled) from Swims where team={} and date={}".format(teamId, date[0]))
			meetScores.append((cursor.fetchone()[0], date[0]))
		c = "c("
		for a in meetScores:
			c += (str(a[0]) + ",")
		c += ")"
		print c
		c = "c("
		for a in meetScores:
			c += (str(a[1]) + ",")
		c += ")"
		print c

# print "Finding outliers"

connection.commit()
connection.close()
print ""
print ""
print "###################"
print "# script complete #"
print "###################"
print "Check {} for results".format(databaseFileName)
print "Written by Kevin Wylder"
print "contact at wylderkevin@gmail.com"
print convertToTimestamp(2014, seasonLineMonth, seasonLineDay)