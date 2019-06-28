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
# Constants for creating and inserting to a table of swim times
CREATE_SWIMS_TABLE = "CREATE TABLE IF NOT EXISTS Swims (swimmer INTEGER, team INTEGER, time REAL, scaled REAL, meet_id INTEGER, event TEXT, date INTEGER, taper INTEGER, snapshot INTEGER);"
INSERT_SWIM_COMMAND = "INSERT INTO Swims VALUES({}, {}, {}, {}, {}, '{}{}', {}, {}, {});"
# Constants for creating and inserting to a table of snapshots NOTE: this seems more like a poorly implemented log...
CREATE_SNAPSHOT_TABLE_COMMAND = "CREATE TABLE IF NOT EXISTS Snapshots (snapshot INTEGER, date TEXT, teams TEXT, events TEXT);"
INSERT_SNAPSHOT_COMMAND = "INSERT INTO Snapshots VALUES({}, '{}', '{}', '{}');"
# Constants for creating and maintaining table of teams
CREATE_TEAM_TABLE = "CREATE TABLE IF NOT EXISTS {} (name TEXT, team_id INTEGER PRIMARY KEY);"
CHECK_TEAM_TABLE = 'SELECT team_id FROM {} WHERE team_id={} LIMIT 1;'
ADD_TO_TEAM_TABLE = "INSERT INTO {} VALUES('{}', {});"
# Constants for creating and maintaining table of swimmers
CREATE_SWIMMER_TABLE = "CREATE TABLE IF NOT EXISTS {} (name TEXT, gender TEXT, swimmer_id INTEGER PRIMARY KEY, team_id INTEGER);"
CHECK_SWIMMER_TABLE = "SELECT swimmer_id FROM {} WHERE swimmer_id={} LIMIT 1;"
ADD_TO_SWIMMER_TABLE = "INSERT INTO {} VALUES('{}', '{}', {}, {});"
# Constants for creating and maintaining table of meets
CREATE_MEET_TABLE = "CREATE TABLE IF NOT EXISTS Meets (meet_id INTEGER PRIMARY KEY, meet_name TEXT, meet_date TEXT, meet_submitted INTEGER, event_dict BLOB);"
CHECK_MEET_TABLE = "SELECT meet_id FROM Meets WHERE meet_id={};"
INSERT_MEET_COMMAND = "INSERT INTO Meets VALUES({}, {}, {}, {}, {});"

# Default inputs for team_dict_generator
DEFAULT_SEASON = "2018-2019"
DEFAULT_GENDER = ["F"]
DEFAULT_EVENTS_TO_PULL = ["M200Y", "11650Y", "1200Y", "2100Y", "3100Y", "4200Y", "150Y", "1100Y", "2200Y", "3200Y",
                          "1500Y", "4100Y", "5200Y", "F200Y"]
DEFAULT_TEAMS_TO_PULL = ["Bucknell University", "Lehigh University"]
DEFAULT_YEAR_START = 2018
DEFAULT_YEAR_END = 2019

# Point Values
INDIVIDUAL_POINTS = [9, 4, 3, 2, 1]
RELAY_POINTS = [11, 4, 2]

