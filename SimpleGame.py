#!/usr/bin/python
#Solves a simple Zero Sum Game for Team A or for Team B
#Learn to use GIT!

from gurobipy import *
import math
import numpy as np
import pandas as pd
from datetime import datetime, date, time
import matplotlib.pyplot as plt
#from process_swim_data import *


def FindOptStrategy(team, payoffmatrix):
    try:
        # Create variables
        numrows = len(payoffmatrix)    # payoff matrix number of rows
        numcols = len(payoffmatrix[0]) # payoff matrix number of columns
        
        if team == "A":
            # Create a new model
            optModelA = Model("TeamAStrategy")

            f = optModelA.addVars(numrows,vtype=GRB.CONTINUOUS, name="f")
            u = optModelA.addVar(vtype=GRB.CONTINUOUS,name="u")

            # Set objective
            optModelA.setObjective(u, GRB.MINIMIZE)

            # Add constraint: sumproduct down rows <= bound u.
            optModelA.addConstrs((quicksum(payoffmatrix[i][j]*f[i] for i in range(numrows)) <= u for j in range(numcols)),"bounds")

            # Add constraint: sum of f  = 1, well defined distribution
            optModelA.addConstr(quicksum(f[i] for i in range(numrows)) == 1, "c1")

            optModelA.optimize()

            policy, value = printSolution(optModelA)

        elif team == "B":
            # Create a new model
            optModelB = Model("TeamBStrategy")

            g = optModelB.addVars(numcols,vtype=GRB.CONTINUOUS, name="g")
            v = optModelB.addVar(vtype=GRB.CONTINUOUS,name="v")

            # Set objective
            optModelB.setObjective(v, GRB.MAXIMIZE)

            # Add constraint: sumproduct down rows <= bound u.
            optModelB.addConstrs((quicksum(payoffmatrix[i][j]*g[j] for j in range(numcols)) >= v for i in range(numrows)),"bounds")

            # Add constraint: sum of f  = 1, well defined distribution
            optModelB.addConstr(quicksum(g[i] for i in range(numcols)) == 1, "c1")
        
            optModelB.optimize()

            policy, value = printSolution(optModelB)

        return policy, value

    except GurobiError as e:
        print('Error code ' + str(e.errno) + ": " + str(e))

    except AttributeError:
        print('Encountered an attribute error')
        
def printSolution(m):
    answer_dic = {}

    for v in m.getVars():
        print('%s %g' % (v.varName, v.x))
        answer_dic.update({v.varName : v.x})

    print('Obj: %g' % m.objVal)

    #return the variables and their optimal values
    return answer_dic, m.objVal

#A function to determine the score using a given lineup for team A versus 
#a given lineup for team B
#def MeetScore(teamAperf,teamAassgn,teamBperf,teamBassgns):

#A function to determine the optimal response lineup for team A versus 
#team B and its selection strategy
#def MeetOpt(teamAperf,teamAassgn,teamBperf,teamBassgns,teamBscenweight):

def PerfRead(ExcelWBName,ExcelWSName):

    #Read in Excel performance times. Remove empty athletes. Convert to total seconds. 
    #Make empty times 1.5 larger than worse athlete in event.
    #teamAperf = {}
    xl = pd.ExcelFile(ExcelWBName)
    df = xl.parse(ExcelWSName)
    df = df.drop([0])
    df = df.rename(columns = {"Your Team\nPredicted Performance":"Athlete Name"})
    df = df.set_index("Athlete Name")
    df = df.dropna(how='all') 
    df = df.replace(r'^\s+$', np.nan, regex=True)
    df = df.fillna(time(0,0,0,0))
    date = str(datetime.strptime("2019-1-1", '%Y-%m-%d').date())  
    for column in df:
        df[column].str.strip()    
        df[column] = pd.to_datetime(date + " " + df[column].astype(str))
        df[column] = df[column].dt.minute*60 + df[column].dt.second + + df[column].dt.microsecond*10**(-6)
        df[column] = df[column].replace(0,1.5*df[column].max())
    
    print(df.head())
    df.plot()
    return df

    #there is a data frame to dictionary tool
    #IF NEEDED LATER
    #read from cells directly
    # d = {}
    # wb = xlrd.open_workbook('foo.xls')
    # sh = wb.sheet_by_index(2)   
    # for i in range(138):
    #     cell_value_class = sh.cell(i,2).value
    #     cell_value_id = sh.cell(i,0).value
    #     d[cell_value_class] = cell_value_id

def AssgnRead(ExcelWBName,ExcelWSName):

    #Read in Excel performance times. Remove empty athletes. Convert to total seconds. 
    #Make empty times 1.5 larger than worse athlete in event.
    #teamAperf = {}
    xl = pd.ExcelFile(ExcelWBName)
    df = xl.parse(ExcelWSName)
    df = df.drop([0])
    df = df.rename(columns = {"Your Team\nPredicted Performance":"Athlete Name"})
    df = df.set_index("Athlete Name")
    df = df.dropna(how='all') 
    df = df.replace(r'^\s+$', np.nan, regex=True)
    df = df.fillna(0) 
    #for column in df: 
    df.plot()
    return df

##########################################################################
## THE ACTUAL PROGRAM  
##########################################################################  
#If the above function is called in this program, run it. If it used as a imported module, the it is ignored 
if __name__ == '__main__':
    #calls the predicted score and lineups as given in the process_swim_data.py code
    #score_matrix = demo_code_with_time_filter()
    score_matrix = [[2, -3], [-3, 4]]
    #Return the Nash equilibrium mixed strategy and expected points for team A and team B.
    f,optA = FindOptStrategy('A', score_matrix)
    g,optB = FindOptStrategy('B', score_matrix)
    print('\n Printing f')
    print(f)
    print('\n Printing optA')
    print(optA)
    print('\n Printing g')
    print(g)
    print('\n Printing optB')
    print(optB)

    #Read in and format the performance data
    #dfperf = PerfRead('HPHS GBN Input Data_PerfandAssignment.xlsx','1. Team Predicted Data Input')
    #dfassgn = AssgnRead('HPHS GBN Input Data_PerfandAssignment.xlsx','Team Assignment')

