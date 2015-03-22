import urllib2
import json
import sqlite3
import datetime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # 
# College Swimming Spring Break Project 2015                                Kevin Wylder #
#                                                                                        #
# This file builds a database from data collected off collegeswimming.com                #
# for more detail on the structure of the database, the global variables in this file,   #
# or the collegeswimming.com website structure, see the README                           #
 # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# search and output parameters
databaseFileName = "database.db"
eventsToPull = ["150Y", "4100Y"]
gendersToPull = ["M"]
seasonsToPull = "2014-2015"
seasonStartTimestamp = 1411171200
teamsToPull = range(400)

swimmerEventUrl = "http://www.collegeswimming.com/swimmer/{}/times/byeventid/{}"
teamRosterUrl = "http://www.collegeswimming.com/team/{}/mod/teamroster?season={}&gender={}"

addTableCommand = "create table if not exists {}{} (name TEXT, date INTEGER, time REAL, team INTEGER, taper INTEGER);"
insertTimeCommand = "insert into {}{} values('{}', {}, {}, {}, {});"

def requestSwimmer(swimmerId):
	'returns the specified swims of this swimmerId'
	swimmerData = []
	for event in eventsToPull:
		url = swimmerEventUrl.format(swimmerId, event)
		page = urllib2.urlopen(url)
		source = page.read()
		eventHistory = json.loads(source)
		for swim in eventHistory:
			# convert the date string to epoch
			splitDate = swim["dateofswim"].split("-")		
			date = (datetime.datetime(int(splitDate[0]), int(splitDate[1]), int(splitDate[2])) - datetime.datetime(1970,1,1)).total_seconds()
			if date > seasonStartTimestamp:
				swimTuple = (event, int(date), swim["time"])
				swimmerData.append(swimTuple)
	return swimmerData

def requestRoster(teamId):
	'returns a list of specified (Name, Gender, swimmerId) tuples for a given teamId'
	teamRoster = []
	for gender in gendersToPull: # men and women rosters have different urls
		url = teamRosterUrl.format(teamId, seasonsToPull, gender)
		try:
			page = urllib2.urlopen(url)
			source = page.read()
		except urllib2.HTTPError:
			return []
		# our own form of parsing. better than using an external library
		rows = source.split("<td><a href=\"/swimmer/")
		for row in rows:
			if "</a></td>" in row:	# having this string ensures good data
				swimmerInfo = row.split("</a></td>")[0]
				swimmerIdSplit = swimmerInfo.split("\">")
				# sanitize the name
				swimmerIdSplit[1] = swimmerIdSplit[1].translate(None, "';\".")
				nameSplit = swimmerIdSplit[1].split(", ")
				teammate = (nameSplit[1] + " " + nameSplit[0], gender, swimmerIdSplit[0])
				teamRoster.append(teammate)
	return teamRoster
				
		
	
##############################
# !!! script starts here !!! #
##############################

# open the sqlite database
connection = sqlite3.connect(databaseFileName)
cursor = connection.cursor()

# create necessary tables
for gender in gendersToPull:
	for event in eventsToPull:
		cursor.execute(addTableCommand.format(gender, event))

raceCounter = 0;
# insert times into table
for teamId in teamsToPull:
	print "TeamId:", teamId, "   Races:", raceCounter
	swimmers = requestRoster(teamId)
	for swimmer in swimmers:
		times = requestSwimmer(swimmer[2])
		raceCounter += len(times)
		for race in times:
			command = insertTimeCommand.format(swimmer[1], race[0], swimmer[0], race[1], race[2], teamId, 0)
			cursor.execute(command)

# save the database
connection.commit()
connection.close()
		