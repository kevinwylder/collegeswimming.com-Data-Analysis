import pandas as pd
import sqlite3
from constants import *
import re
# This file is for processing the data


def get_data():
    """
    :return: swims, swimmers, teams, raw data from collegeswimming website.
    """
    connection = sqlite3.connect(DATABASE_FILE_NAME)
    swims = pd.read_sql_query("SELECT * FROM Swims", connection)
    swimmers = pd.read_sql_query("SELECT * FROM Swimmers", connection).rename({"name": "athlete_name"}, axis="columns")
    teams = pd.read_sql_query("SELECT * FROM Teams", connection).rename({"name": "team_name"}, axis="columns")
    connection.close()

    event_list = list(swims["event"].unique())  # TODO: this should come from user input in the future
    full_dataset = swims.join(swimmers.set_index('swimmer_id'), on='swimmer').join(teams.set_index('team_id'), on='team')
    grouped_dataset = full_dataset.groupby("swimmer")
    # TODO: use this instead of swims as return value when you feel ready ^^
    return swims, swimmers, teams, event_list


def get_athlete_data(swims, swimmers, teams, event_list):
    """
    :param swims: dataframe containing data on individual swims
    :param swimmers: dataframe with names and IDs of swimmers
    :param event_list: list of events included in the dataset
    :return: team_data, a dataframe of all swimmers, as well as different measures of their performance
    """
    full_dataset = swims.join(swimmers.set_index('swimmer_id'), on='swimmer').join(teams.set_index('team_id'), on='team')
    grouped_dataset = full_dataset.groupby(["swimmer", "event"])
    team_data = []
    swimmer_event_pairs_used = grouped_dataset.groups.keys()
    swimmers.set_index("swimmer_id", inplace=True)
    teams.set_index("team_id", inplace=True)
    for swimmer, swimmer_data in swimmers.iterrows():
        athlete_name = swimmer_data["athlete_name"]
        team = teams.loc[swimmer_data["team_id"]]["team_name"]
        for event in event_list:
            if (swimmer, event) not in swimmer_event_pairs_used:
                team_data.append({"athlete_name": athlete_name, "event": event, "team": team, "minimum_time": None,
                                  "average_time": None, "median_time": None})
            else:
                individual_event_data = grouped_dataset.get_group((swimmer, event))
                minimum_time = individual_event_data["time"].min()
                average_time = individual_event_data["time"].mean()
                median_time = individual_event_data["time"].median()
                team_data.append({"athlete_name": athlete_name, "event": event, "team": team,
                                  "minimum_time": minimum_time, "average_time": average_time, "median_time": median_time})

    team_data = pd.DataFrame(team_data, columns=["athlete_name", "event", "team", "minimum_time", "average_time", "median_time"])
    # This will have every possible athlete-event pairing possible, even if an athlete hasn't done that event before
    return team_data


def get_predicted_performance_matrix(team_data, preference):
    """
    Inputs:
    1. team_data, a pandas data frame containing information on a group (or groups) of athletes.
    2. preference, a string indicating the information in team_data that you wish to use to find an optimal team lineup
    Outputs:
    athlete_prediction_dictionary, a dictionary of athletes and their predicted performances
    """
    # NOTE: In the future when we decide how this information is input, there should be a dictionary that converts
    #  different input types to be equal to these values (i.e. {"minimum : MIN,...}), or the reverse of this
    # NOTE: It also might be a good idea to use athlete ID instead of name somewhere in case two team members have the
    #  same name, but that is a problem for another time

    group_by_individual = team_data.groupby("athlete_name")  # should uniquely identify every player

    athlete_prediction_dictionary = {}
    for athlete, athlete_data in group_by_individual:
        individual_data = athlete_data[["event",preference]].transpose()
        individual_data.columns = individual_data.iloc[0]
        individual_data.drop("event", inplace=True)
        athlete_prediction_dictionary[athlete] = individual_data.to_dict('records')[0]
    return athlete_prediction_dictionary


def get_team_lineup(swims, swimmers, teams, event_list, meet_id):
    """
    :param swims: raw data on individual swims in a dataframe.
    :param swimmers: dataframe of swimmer names and IDs
    :param event_list: the list of events that are included in the dataset
    :param meet_id: this is a numerical ID
    :return: meet_lineup, the lineup used by one team at a single meet. this is a dictionary with the format
    {athlete_name: {"event1": (1 or 0), "event2": (1 or 0),...}} with 1 showing that an athlete participated in an event
    and 0 indicating that they did not

    The purpose of this function is to find a previous lineup used by a given team.
    """

    filter_by_meet = swims[swims["meet_id"] == meet_id].copy()  # works without copy() but will throw a warning
    filter_by_meet['time'] = filter_by_meet['time'].notna().astype(int)

    group_by_individual = filter_by_meet.groupby("swimmer")

    event_dict = {event: 0 for event in event_list}

    meet_lineup = {}
    # makes a nested dictionary containing all athletes and events. all values in event dicts are False (0)
    for swimmer, swimmer_data in swimmers.iterrows():
        athlete_name = swimmer_data["athlete_name"]
        meet_lineup[athlete_name] = event_dict.copy()

    # updates the dictionary made above so that events an athlete participated in are True (1)
    for swimmer, swimmer_data in group_by_individual:
        athlete_name = swimmers.loc[swimmer]["athlete_name"]
        print(swimmer_data[["event","time"]])
        individual_data = swimmer_data[["event","time"]].transpose()
        individual_data.columns = individual_data.iloc[0]
        individual_data.drop("event", inplace=True)
        meet_lineup[athlete_name].update(individual_data.to_dict('records')[0])
    return meet_lineup


def calculate_pred_score(perfA, lineA, perfB, lineB):
    """
    returns the predicted score of team A for a swimming meet
    :param perfA: Pandas dataframe of predicted performances for a given team A's swimmers
    :param lineA: Pandas Dataframe of a given lineup for a team A
    :param perfB: Pandas dataframe of predicted performances for a given team B's swimmers
    :param lineB: Pandas Dataframe of a given lineup for a team B
    :return: pred_score: Integer value of team A's predicted
    """
    # This is a predicted performance matrix that only contains values for swimmers in the lineup
    lineup_scoresA = perfA[lineA==1]
    lineup_scoresB = perfB[lineB==1]
    # Dictionaries for storing relay times
    medley_total_times_A = {}
    medley_total_times_B = {}
    free_total_times_A = {}
    free_total_times_B = {}
    # Team scores are integer values
    score_A = 0
    score_B = 0
    # This assumes that team A and B both have their event columns in the same order
    for column_name in lineup_scoresA:
        column_vals_A = lineup_scoresA[column_name][lineup_scoresA[column_name].notna()].tolist()
        column_vals_B = lineup_scoresA[column_name][lineup_scoresB[column_name].notna()].tolist()
        if column_name[2] in "M":  # Relay race
            # column_name[2] is medley vs free, column_name[-1] is team A,B,C,etc
            if (column_name[2]+column_name[-1]) not in medley_total_times_A:
                medley_total_times_A[column_name[2] + column_name[-1]] = sum(column_vals_A)
                medley_total_times_B[column_name[2] + column_name[-1]] = sum(column_vals_B)
            else:
                medley_total_times_A[column_name[2]+column_name[-1]] += sum(column_vals_A)
                medley_total_times_B[column_name[2]+column_name[-1]] += sum(column_vals_B)
        elif column_name[2] in "F":  # Relay race
            # column_name[2] is medley vs free, column_name[-1] is team A,B,C,etc
            if (column_name[2]+column_name[-1]) not in free_total_times_A:
                free_total_times_A[column_name[2] + column_name[-1]] = sum(column_vals_A)
                free_total_times_B[column_name[2] + column_name[-1]] = sum(column_vals_B)
            else:
                free_total_times_A[column_name[2]+column_name[-1]] += sum(column_vals_A)
                free_total_times_B[column_name[2]+column_name[-1]] += sum(column_vals_B)
        else:  # Individual race
            for place in INDIVIDUAL_POINTS:
                if len(column_vals_A) > 0 and len(column_vals_B) > 0:
                    if min(column_vals_A) < min(column_vals_B):
                        column_vals_A.remove(min(column_vals_A))
                        score_A += place
                        print("awarded {} points to team A for event {}".format(place, column_name))
                    else:
                        column_vals_B.remove(min(column_vals_B))
                        score_B += place
                        print("awarded {} points to team B for event {}".format(place, column_name))
                elif len(column_vals_A) > 0:
                    column_vals_A.pop()
                    score_A += place
                elif len(column_vals_B) > 0:
                    column_vals_B.pop()
                    score_B += place
                else:
                    continue
        # Add in scores for relays
        scores_medley_A = list(medley_total_times_A.values())
        scores_medley_B = list(medley_total_times_B.values())
        for val in range(len(scores_medley_A)):
            if scores_medley_A[val] == 0:
                scores_medley_A[val] = 9001
            if scores_medley_B[val] == 0:
                scores_medley_B[val] = 9001
        for place in RELAY_POINTS:
            if len(scores_medley_A) > 0 and len(scores_medley_B) > 0:
                if min(scores_medley_A) < min(scores_medley_B):
                    scores_medley_A.remove(min(scores_medley_A))
                    score_A += place
                    print("awarded {} points to team A for medley".format(place))
                else:
                    scores_medley_B.remove(min(scores_medley_B))
                    score_B += place
                    print("awarded {} points to team B for medley".format(place))
            elif len(scores_medley_A) > 0:
                scores_medley_A.pop()
                score_A += place
            elif len(scores_medley_B) > 0:
                scores_medley_B.pop()
                score_B += place
            else:
                continue
        scores_free_A = list(free_total_times_A.values())
        scores_free_B = list(free_total_times_B.values())
        for val in range(len(scores_free_A)):
            if scores_free_A[val] == 0:
                scores_free_A[val] = 9001
            if scores_free_B[val] == 0:
                scores_free_B[val] = 9001
        for place in RELAY_POINTS:
            if len(scores_free_A) > 0 and len(scores_free_B) > 0:
                if min(scores_free_A) < min(scores_free_B):
                    scores_free_A.remove(min(scores_free_A))
                    score_A += place
                    print("awarded {} points to team A for free".format(place))

                else:
                    scores_free_B.remove(min(scores_free_B))
                    score_B += place
                    print("awarded {} points to team A for free".format(place))

            elif len(scores_free_A) > 0:
                scores_free_A.pop()
                score_A += place
            elif len(scores_free_B) > 0:
                scores_free_B.pop()
                score_B += place
            else:
                continue
    print(score_A)
    print(score_B)
    print(lineup_scoresA.columns)
    return score_A, score_B


def score_event(results_a, results_b, places):
    """
    assigns points to groups based on who has the smallest score/time.
    :param results_a: list of recorded times for team a
    :param results_b: list of recorded times for team b
    :param places: list of point values awarded for first, second, etc place
    :return: scores of team a and b
    """
    score_a = score_b = 0
    for place in places:
        if len(results_a) > 0 and len(results_b) > 0:
            if min(results_a) < min(results_b):
                results_a.remove(min(results_a))
                score_a += place
            else:
                results_b.remove(min(results_b))
                score_b += place
        elif len(results_a) > 0:
            results_a.pop()
            score_a += place
        elif len(results_b) > 0:
            results_b.pop()
            score_b += place
        else:
            continue
    return score_a, score_b


def calculate_pred_score_try(perfA, lineA, perfB, lineB):
    """
    returns the predicted score of team A for a swimming meet
    :param perfA: Pandas dataframe of predicted performances for a given team A's swimmers
    :param lineA: Pandas Dataframe of a given lineup for a team A
    :param perfB: Pandas dataframe of predicted performances for a given team B's swimmers
    :param lineB: Pandas Dataframe of a given lineup for a team B
    :return: pred_score: Integer value of team A's predicted
    """
    # This is a predicted performance matrix that only contains values for swimmers in the lineup
    lineup_scores_a = perfA[lineA==1]
    lineup_scores_b = perfB[lineB==1]
    # Team scores are integer values
    score_a = score_b = 0
    # Find times for all relay events and put them together in one dictionary
    event_list = lineup_scores_a.columns.tolist()
    r = re.compile(".L[MF].+")  # look for relay events
    relay_list = list(filter(r.match, event_list))
    relay_event_results = dict()
    for value in relay_list:
        if value[2] is "F":
            legs = [value, value[:1]+"1"+value[2:]]
        elif value[2] is "M":
            legs = [value, value[:1] + "2" + value[2:], value[:1] + "3" + value[2:], value[:1] + "4" + value[2:]]
        time_a = lineup_scores_a[legs].sum().sum()
        time_b = lineup_scores_b[legs].sum().sum()
        # if event is in dictionary, update data, if not then add it
        if value[2:-1] in relay_event_results:
            if time_a != 0:
                relay_event_results[value[2:-1]][0].append(time_a)
            if time_b != 0:
                relay_event_results[value[2:-1]][1].append(time_b)
        else:
            relay_event_results[value[2:-1]] = [[time_a],[time_b]]
            if time_a == 0:
                relay_event_results[value[2:-1]][0].pop()
            if time_b == 0:
                relay_event_results[value[2:-1]][1].pop()

    # score the relays
    for event in relay_event_results:
        # get results for each team by event
        results_a = relay_event_results[event][0]
        results_b = relay_event_results[event][1]
        tempa, tempb = score_event(results_a, results_b, RELAY_POINTS)
        score_a += tempa
        score_b += tempb
    # score individual events
    individual_events = list(filter(lambda x: x[2] not in "MF", event_list))
    for column_name in individual_events:
        column_vals_a = lineup_scores_a[column_name][lineup_scores_a[column_name].notna()].tolist()
        column_vals_b = lineup_scores_a[column_name][lineup_scores_b[column_name].notna()].tolist()
        tempa, tempb = score_event(column_vals_a, column_vals_b, INDIVIDUAL_POINTS)
        score_a += tempa
        score_b += tempb
    print(score_a)
    print(score_b)

def demo_code():
    bucknell_vs_lehigh = 119957
    swims, swimmers, teams, event_list = get_data()
    team_data = get_athlete_data(swims, swimmers, teams, event_list)
    pred_perfA = get_predicted_performance_matrix(team_data, 'minimum_time')
    some_lineupA = get_team_lineup(swims, swimmers, teams, event_list, bucknell_vs_lehigh)
    pred_perfB = get_predicted_performance_matrix(team_data, 'average_time')
    some_lineupB = get_team_lineup(swims, swimmers, teams, event_list, 104421)
    print("\n predicted performance of players (based on average time)\n")
    print(pd.DataFrame.from_dict(pred_perfA, orient='index'))
    print("\n lineup used during meet {0} (meet names will be incorporated later, for now here is the url that will "
          "lead to that event: https://www.collegeswimming.com/results/{0}/\n".format(bucknell_vs_lehigh))
    print(pd.DataFrame.from_dict(some_lineupA, orient='index'))
    pred_perfA = pd.DataFrame.from_dict(pred_perfA, orient='index')
    some_lineupA = pd.DataFrame.from_dict(some_lineupA, orient='index')
    pred_perfB = pd.DataFrame.from_dict(pred_perfB, orient='index')
    some_lineupB = pd.DataFrame.from_dict(some_lineupB, orient='index')
    calculate_pred_score(pred_perfA, some_lineupA, pred_perfB, some_lineupB)
    calculate_pred_score_try(pred_perfA, some_lineupA, pred_perfB, some_lineupB)


demo_code()