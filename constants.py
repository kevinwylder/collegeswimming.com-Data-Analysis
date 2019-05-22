##########################################################
# Constants for team_dict_generator.py                   #
##########################################################
MAX_TEAM_ID = 9826

##########################################################
# Global Parameters needed for database. Must re-run     #
#    team_dict_generator if you change these             #
##########################################################
DATABASE_FILE_NAME = "./collegeswimming.db"
SEASON_LINE_MONTH = 9
SEASON_LINE_DAY = 15

##########################################################
# Constants for team_dict_generator                      #
##########################################################

# URL's for pulling data from
SWIMMER_URL = "https://www.collegeswimming.com/swimmer/{}"
SWIMMER_EVENT_URL = "https://www.collegeswimming.com/swimmer/{}/times/byeventid/{}"
ROSTER_URL = "https://www.collegeswimming.com/team/{}/roster?season={}&gender={}"

#Missing data in createXYZTable is filled in by data put into insertXYZCommand using .format()
CREATE_SWIMS_TABLE = "create table if not exists Swims (swimmer INTEGER, team INTEGER, time REAL, scaled REAL, event TEXT, date INTEGER, taper INTEGER, snapshot INTEGER);"
INSERT_SWIM_COMMAND = "insert into Swims values({}, {}, {}, {}, '{}{}', {}, {}, {});"
CREATE_SNAPSHOT_TABLE_COMMAND = "create table if not exists Snapshots (snapshot INTEGER, date TEXT, teams TEXT, events TEXT);"
INSERT_SNAPSHOT_COMMAND = "insert into Snapshots values({}, '{}', '{}', '{}');"
CREATE_NAME_TABLE = "create table if not exists {} (name TEXT, id INTEGER);"
CHECK_NAME_TABLE = 'select id from {} where id={} limit 1;'
ADD_TO_NAME_TABLE = "insert into {} values('{}', {});"

# Default inputs for team_dict_generator
DEFAULT_SEASON = "2017-2018"
DEFAULT_GENDER = ["M"]
DEFAULT_EVENTS_TO_PULL = ["150Y", "1100Y"]
DEFAULT_TEAMS_TO_PULL = [184]
DEFAULT_YEAR_START = 2017
DEFAULT_YEAR_END = 2018

# Analysis Parameters (I haven't seen this part of the code yet so I don't really know what this is for
EVENT_HISTOGRAMS = ["F5200Y"]
TEAMS_TO_REVIEW = [184]
SWIMMERS_TO_REVIEW = [325120]
REVIEW_YEAR_START = 2017
REVIEW_YEAR_END = 2018

TEAM_URL = "https://www.collegeswimming.com/team/{}"

