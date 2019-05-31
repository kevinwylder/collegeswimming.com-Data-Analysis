import subprocess
import sqlite3
from constants import *
import helperfunctions as hf

# This script is just a wrapper for the R scripts. They have a lot of parameters that need
# unix timestamps, and it's just easier to generate them in a loop


# start by making event histograms
# go through each specified event
print ("")
print ("")
print ("Graphing event Histograms...")
for event in EVENT_HISTOGRAMS:
	title = hf.toTitle(event)
	database = DATABASE_FILE_NAME
	process = ["Rscript", "histogram_event.R", event, title, database]
	subprocess.call(process)

print ("done")
print ("")
print ("")

# we need the database to get names from here on out
connection = sqlite3.connect(DATABASE_FILE_NAME)
cursor = connection.cursor()
print ("Graphing team History...")
for team in TEAMS_TO_REVIEW:
	# get the team name
	cursor.execute("select name from Teams where id={}".format(team))
	teamName = cursor.fetchone()[0]
	startTimestamp = hf.convertToTime(REVIEW_YEAR_START, SEASON_LINE_MONTH, SEASON_LINE_DAY)
	endTimestamp = hf.convertToTime(REVIEW_YEAR_END, SEASON_LINE_MONTH, SEASON_LINE_DAY)
	# run the whole history graphing script
	process = ["Rscript", "team_history.R", str(team), teamName, str(startTimestamp), str(endTimestamp), database]
	subprocess.call(process)
	# run each year's meet analysis
	for simpleYear in range(REVIEW_YEAR_START, REVIEW_YEAR_END):
		startTimestamp = hf.convertToTime(simpleYear, SEASON_LINE_MONTH, SEASON_LINE_DAY)
		endTimestamp = hf.convertToTime(simpleYear + 1, SEASON_LINE_MONTH, SEASON_LINE_DAY)
		title = "{} {}-{} Season".format(teamName, simpleYear, simpleYear + 1)
		process = ["Rscript", "team_season.R", str(team), title, str(startTimestamp), str(endTimestamp), database]
		subprocess.call(process)

print ("done")
print ("")
print ("")

print ("Graphing Individual Season")
for swimmer in SWIMMERS_TO_REVIEW:
	# get the swimmer's name
	cursor.execute("select name from Swimmers where id={}".format(swimmer))
	name = cursor.fetchone()[0]
	for simpleYear in range(REVIEW_YEAR_START, REVIEW_YEAR_END):
		# graph each year
		startTimestamp = hf.convertToTime(simpleYear, SEASON_LINE_MONTH, SEASON_LINE_DAY)
		endTimestamp = hf.convertToTime(simpleYear + 1, SEASON_LINE_MONTH, SEASON_LINE_DAY)
		title = "{}'s {}-{} Season".format(name, simpleYear, simpleYear + 1)
		process = ["Rscript", "individual_season.R", str(swimmer), title, str(startTimestamp), str(endTimestamp), DATABASE_FILE_NAME]
		subprocess.call(process)
