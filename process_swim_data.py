import pandas as pd
import sqlite3
from constants import *

def getAthleteData():
    connection = sqlite3.connect(DATABASE_FILE_NAME)
    SWIMS = pd.read_sql_query("SELECT * FROM Swims", connection)
    SWIMMERS = pd.read_sql_query("SELECT * FROM Swimmers", connection).rename({"name":"athlete_name"},axis="columns")
    TEAMS = pd.read_sql_query("SELECT * FROM Teams", connection).rename({"name":"team_name"},axis="columns")
    connection.close()

    full_dataset = SWIMS.join(SWIMMERS.set_index('id'), on='swimmer').join(TEAMS.set_index('id'), on='team')
    grouped_dataset = full_dataset.groupby(["swimmer", "event"])
    eventlist = list(full_dataset["event"].unique())#can speed this up by simply setting it equal to user input for events
    team_data = []
    for swimmer in SWIMMERS["id"]:
        for event in eventlist:
            athlete_name = SWIMMERS[SWIMMERS['id']==swimmer]["athlete_name"].tolist()[0]#there has to be a better way to do this
            try:
                individual_event_data = grouped_dataset.get_group((swimmer, event))
                team = individual_event_data[individual_event_data["swimmer"] == swimmer]["team_name"].unique().tolist()#there has to be a better way to do this
                minimum_time = individual_event_data["time"].min()
                average_time = individual_event_data["time"].mean()
                team_data.append({"athlete_name":athlete_name, "event":event, "team":team, "minimum_time":minimum_time, "average_time":average_time})
            except KeyError as e:
                team = full_dataset[full_dataset["swimmer"] == swimmer]["team_name"].unique().tolist()#there has to be a better way to do this
                team_data.append({"athlete_name":athlete_name, "event":event, "team":team, "minimum_time":None, "average_time":None})

    team_data = pd.DataFrame(team_data, columns = ["athlete_name","event","team","minimum_time","average_time"])
    return team_data

def getAthletePredictedPerformance(team_data, preference):
    """
    Inputs:
    1. team_data, a pandas dataframe containing information on a group (or groups) of athletes.
    2. preference, a string indicating the information in team_data that you wish to use to find an optimal team lineup
    Outputs:
    athletePredPerf, a dictionary of athletes and their predicted performances
    """
    if (preference == "minimum"):
        athletePredPerf = 
    elif (preference == "average"):
