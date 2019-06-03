import pandas as pd
import sqlite3
from constants import *
# This file is for processing the data


def get_athlete_data():
    connection = sqlite3.connect(DATABASE_FILE_NAME)
    swims = pd.read_sql_query("SELECT * FROM Swims", connection)
    swimmers = pd.read_sql_query("SELECT * FROM Swimmers", connection).rename({"name":"athlete_name"},axis="columns")
    teams = pd.read_sql_query("SELECT * FROM Teams", connection).rename({"name":"team_name"},axis="columns")
    connection.close()

    full_dataset = swims.join(swimmers.set_index('id'), on='swimmer').join(teams.set_index('id'), on='team')
    grouped_dataset = full_dataset.groupby(["swimmer", "event"])
    event_list = list(full_dataset["event"].unique())  # can speed this up by  setting it equal to user input for events
    team_data = []
    for swimmer in swimmers["id"]:
        for event in event_list:
            athlete_name = swimmers[swimmers['id']==swimmer]["athlete_name"].tolist()[0]  # try to find better way to do
            try:
                individual_event_data = grouped_dataset.get_group((swimmer, event))
                team = individual_event_data[individual_event_data["swimmer"] == swimmer]["team_name"].unique().tolist()
                # NOTE: there has to be a better way to do this ^^
                minimum_time = individual_event_data["time"].min()
                average_time = individual_event_data["time"].mean()
                team_data.append({"athlete_name":athlete_name, "event":event, "team":team, "minimum_time":minimum_time,
                                  "average_time":average_time})
            except KeyError as e:
                team = full_dataset[full_dataset["swimmer"] == swimmer]["team_name"].unique().tolist()
                # NOTE: there has to be a better way to do this ^^
                team_data.append({"athlete_name":athlete_name, "event":event, "team":team, "minimum_time":None,
                                  "average_time":None})

    team_data = pd.DataFrame(team_data, columns = ["athlete_name","event","team","minimum_time","average_time"])
    # This will have every possible athlete-event pairing possible, even if an athlete hasn't done that event before
    return team_data


def get_athlete_predicted_performance(team_data, preference):
    """
    Inputs:
    1. team_data, a pandas data frame containing information on a group (or groups) of athletes.
    2. preference, a string indicating the information in team_data that you wish to use to find an optimal team lineup
    Outputs:
    athlete_prediction_dictionary, a dictionary of athletes and their predicted performances
    """
    # NOTE: In the future when we decide how this information is input, there should be a dictionary that converts
    # different input types to be equal to these values (i.e. {"minimum : MIN,...}), or the reverse of this
    # NOTE: It also might be a good idea to use athlete ID instead of name somewhere in case two team members have the
    # same name, but that is a problem for another time

    group_by_individual = team_data.groupby("athlete_name")  # should uniquely identify every player

    athlete_prediction_dictionary = {}
    for athlete, athlete_data in group_by_individual:
        individual_data = athlete_data[["event",preference]].transpose()
        individual_data.columns = individual_data.iloc[0]
        individual_data.drop("event", inplace=True)
        athlete_prediction_dictionary[athlete] = individual_data.to_dict('records')[0]

    return athlete_prediction_dictionary


get_athlete_predicted_performance(get_athlete_data(), "minimum_time")
