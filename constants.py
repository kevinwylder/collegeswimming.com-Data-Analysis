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
ROSTER_URL = "https://www.collegeswimming.com/team/{}/roster/?page=1&gender={}&season={}"
RESULTS_URL = "https://www.collegeswimming.com/team/{}/results/?page=1&name=&meettype=&season={}"
MEET_URL = "https://www.collegeswimming.com/results/{}/?gender={}"
MEET_EVENT_URL = "https://www.collegeswimming.com/results/{}/event/{}/"
SPLASH_SPLITS_URL = "https://www.collegeswimming.com/times/{}/splashsplits/"

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
CREATE_MEET_TABLE = "CREATE TABLE IF NOT EXISTS Meets (meet_id INTEGER, meet_name TEXT, meet_date TEXT, meet_submitted INTEGER);"
CHECK_MEET_TABLE = "SELECT meet_id FROM Meets WHERE meet_id={};"
INSERT_MEET_COMMAND = "INSERT INTO Meets VALUES({}, {}, {}, {});"

#INSERT INTO Meets VALUES({}, {}, {}, {}) ON CONFLICT(meet_id) DO UPDATE SET age=excluded.age;




########################################################################################################################
#                               DEFAULT INPUTS FOR get_swim_data. CAN CHANGE HERE                                      #
########################################################################################################################
# Default inputs for get_swim_data.py
DEFAULT_SEASON = "2018-2019"
DEFAULT_GENDER = ["F"]
DEFAULT_EVENTS_TO_PULL = ["M200Y", "11650Y", "1200Y", "2100Y", "3100Y", "4200Y", "150Y", "1100Y", "2200Y", "3200Y",
                          "1500Y", "4100Y", "5200Y", "F200Y"]
DEFAULT_TEAMS_TO_PULL = ["Bucknell University", "Lehigh University"]
DEFAULT_YEAR_START = 2017
DEFAULT_YEAR_END = 2018

########################################################################################################################
#                                 SCORING RULES FOR process_swim_data CAN BE CHANGED HERE                              #
########################################################################################################################
# Point Values for each place in an event category. Format: {# of Lanes: [1st place, 2nd place,... nth place]}
INDIVIDUAL_POINTS = {"Six Lane": [9, 4, 3, 2, 1, 0], "Five Lane": [5, 3, 1, 0]}
RELAY_POINTS = {"Six Lane": [11, 4, 2], "Five Lane": [7, 0]}
# Limit for number of people who can score per team in each event type. Format: {# of Lanes: [Individual, Relay]}
SCORER_LIMIT = {"Six Lane": [3,2], "Five Lane": [2,1]}

#
#SCORING_CONSTRAINTS = {"Dual": {"Six": {"Individual": [9, 4, 3, 2, 1], "Relay": [11, 4, 2], "Limit": [3, 2]},
#                                "Five": {"Individual": [5, 3, 1], "Relay": [7, 0], "Limit": [2, 1]}},
#                       "Double Dual": {"Nine": {"Individual": [9, 4, 3, 2, 1], "Relay": [11, 4, 2], "Limit": [3,2]},
#                                       "Eight": {"Individual": [9, 4, 3, 2, 1], "Relay": [11, 4, 2], "Limit": [3,2]}},
#                       "Triangular": ""}