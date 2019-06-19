##########################################################
# Global Parameters needed for database. Must re-run     #
# get_swim_data if you change these                      #
##########################################################
DATABASE_FILE_NAME = "./collegeswimming.db"
SEASON_LINE_MONTH = 9
SEASON_LINE_DAY = 15

##########################################################
# Constants for get_team_data                            #
##########################################################

# URL's for pulling data from
SWIMMER_URL = "https://www.collegeswimming.com/swimmer/{}"
SWIMMER_EVENT_URL = "https://www.collegeswimming.com/swimmer/{}/times/byeventid/{}"
ROSTER_URL = "https://www.collegeswimming.com/team/{}/roster?season={}&gender={}"

# Missing data in createXYZTable is filled in by data put into insertXYZCommand using .format()
CREATE_SWIMS_TABLE = "CREATE TABLE IF NOT EXISTS Swims (swimmer INTEGER, team INTEGER, time REAL, scaled REAL, meet_id INTEGER, event TEXT, date INTEGER, taper INTEGER, snapshot INTEGER);"
INSERT_SWIM_COMMAND = "INSERT INTO Swims VALUES({}, {}, {}, {}, {}, '{}{}', {}, {}, {});"
CREATE_SNAPSHOT_TABLE_COMMAND = "CREATE TABLE IF NOT EXISTS Snapshots (snapshot INTEGER, date TEXT, teams TEXT, events TEXT);"
INSERT_SNAPSHOT_COMMAND = "INSERT INTO Snapshots VALUES({}, '{}', '{}', '{}');"
CREATE_NAME_TABLE = "CREATE TABLE IF NOT EXISTS {} (name TEXT, id INTEGER);"
CHECK_NAME_TABLE = 'SELECT id FROM {} WHERE id={} LIMIT 1;'
ADD_TO_NAME_TABLE = "INSERT INTO {} VALUES('{}', {});"

# Default inputs for team_dict_generator
DEFAULT_SEASON = "2017-2018"
DEFAULT_GENDER = ["F", "M"]
DEFAULT_EVENTS_TO_PULL = ["M200Y", "11650Y", "1200Y", "2100Y", "3100Y", "4200Y", "150Y", "1100Y", "2200Y", "3200Y",
                          "1500Y", "4100Y", "5200Y", "F200Y"]
DEFAULT_TEAMS_TO_PULL = ["Bucknell University"]
DEFAULT_YEAR_START = 2017
DEFAULT_YEAR_END = 2018

##########################################################
# Constants for analysis.py                              #
##########################################################

# Analysis Parameters (I haven't seen this part of the code yet so I don't really know what this is for
EVENT_HISTOGRAMS = ["M1100Y"]  # should be an input you can change
TEAMS_TO_REVIEW = [184]  # should be an input you can change
SWIMMERS_TO_REVIEW = [325120]  # should be an input you can change
REVIEW_YEAR_START = 2017  # should be an input you can change
REVIEW_YEAR_END = 2018  # should be an input you can change


