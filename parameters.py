import datetime

class Parameters:

	# explanations of these parameters can be found in the README
	
	# Global Parameters. If you change these, delete the database and re-run main.py
	databaseFileName = "collegeswimming.db"
	seasonLineMonth = 9
	seasonLineDay = 15
	
	# main.py parameters
	eventsToPull = ["2200Y", "4200Y", "5200Y", "5400Y"]
	gendersToPull = ["M", "F"]
	teamsToPull = [51, 107, 116, 121, 131, 154, 155, 188, 194, 261, 362, 337, 384, 385, 390, 417, 447, 496, 497, 499, 517, 528, 542, 639]
	yearStart = 2010
	yearEnd = 2015
	
	# analysis parameters
	eventHistograms = []
	teamsToReview = [121]
	swimmersToReview = [195199,192288]
	reviewYearStart = 2010
	reviewYearEnd = 2015
	
	
	def convertToTimestamp(self, year, month, day):
		'converts a given month day and year into a timestamp. Why is this so hard?'
		return (datetime.datetime(int(year), int(month), int(day)) - datetime.datetime(1970,1,1)).total_seconds()

	
	def toTitle(self,eventString):
		'converts an event string into a human readable title'
		gender = eventString[0]
		stroke = eventString[1]
		distance = eventString[2:-1]
		genderMap = {"M":"Men", "F":"Women"}
		strokeMap = {"1":"Freestyle", "2":"Backstroke", "3":"Breaststroke", "4":"Butterfly", "5":"IM"}
		return "{}'s {} Yard {}".format(genderMap[gender], distance, strokeMap[stroke])
		