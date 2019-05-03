import parameters
import subprocess
import sqlite3

# This script is just a wrapper for the R scripts. They have a lot of parameters that need
# unix timestamps, and it's just easier to generate them in a loop

parameters = parameters.Parameters() # buffalo

# start by making event histograms
# go through each specified event
print ("")
print ("")
print ("Graphing event Histograms...")
for event in parameters.eventHistograms:
	title = parameters.toTitle(event)
	database = parameters.databaseFileName
	process = ["Rscript", "histogram_event.R", event, title, database]
	subprocess.call(process)

print ("done")
print ("")
print ("")

# we need the database to get names from here on out
connection = sqlite3.connect(parameters.databaseFileName)
cursor = connection.cursor()
print ("Graphing team History...")
for team in parameters.teamsToReview:
	# get the team name
	cursor.execute("select name from Teams where id={}".format(team))
	teamName = cursor.fetchone()[0]
	startTimestamp = parameters.convertToTimestamp(parameters.reviewYearStart, parameters.seasonLineMonth, parameters.seasonLineDay)
	endTimestamp = parameters.convertToTimestamp(parameters.reviewYearEnd, parameters.seasonLineMonth, parameters.seasonLineDay)
	# run the whole history graphing script
	process = ["Rscript", "team_history.R", str(team), teamName, str(startTimestamp), str(endTimestamp), database]
	subprocess.call(process)
	# run each year's meet analysis
	for simpleYear in range(parameters.reviewYearStart, parameters.reviewYearEnd):
		startTimestamp = parameters.convertToTimestamp(simpleYear, parameters.seasonLineMonth, parameters.seasonLineDay)
		endTimestamp = parameters.convertToTimestamp(simpleYear + 1, parameters.seasonLineMonth, parameters.seasonLineDay)
		title = "{} {}-{} Season".format(teamName, simpleYear, simpleYear + 1)
		process = ["Rscript", "team_season.R", str(team), title, str(startTimestamp), str(endTimestamp), database]
		subprocess.call(process)

print ("done")
print ("")
print ("")

print ("Graphing Individual Season")
for swimmer in parameters.swimmersToReview:
	# get the swimmer's name
	cursor.execute("select name from Swimmers where id={}".format(swimmer))
	name = cursor.fetchone()[0]
	for simpleYear in range(parameters.reviewYearStart, parameters.reviewYearEnd):
		# graph each year
		startTimestamp = parameters.convertToTimestamp(simpleYear, parameters.seasonLineMonth, parameters.seasonLineDay)
		endTimestamp = parameters.convertToTimestamp(simpleYear + 1, parameters.seasonLineMonth, parameters.seasonLineDay)
		title = "{}'s {}-{} Season".format(name, simpleYear, simpleYear + 1)
		process = ["Rscript", "individual_season.R", str(swimmer), title, str(startTimestamp), str(endTimestamp), parameters.databaseFileName]
		subprocess.call(process)
