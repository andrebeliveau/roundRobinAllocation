#!/usr/bin/env python3
import argparse
from datetime import datetime
import json
import math
from operator import mod
import random
from ortools.sat.python import cp_model

"""

Scheduling of friendly games for players sharing tennis courts (double games).
Part 3:  Shuffle/Assign specific court to each group of players

Input:
    number of tennis courts available
    number of players available (some players might sit on bench on some games )
    number of rounds (turn) to be played
    file containing set of players on each round 
        input as groups_{fname}
        output as final_{fname}

    file containing set of players on bench on each round (outputed by bench_sat.py)

Objective:
    Every player should have a chance to play with or against every other player
    Every player should play an equal number of rounds
    Every player should have an equal (or almost) number of rounds sitting on bench
    Sitting on bench should not occur too quickly (e.g. not 2 consecutive rounds on bench)
    Every player should not play with the same player more than once, but he/she could
        play against him/her multiple times

"""

class PlayersPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""
    def __init__(self, games, group_assignements, groupVar, num_players, num_rounds, num_courts, limit, \
        groups, bench_matrix):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._games = games
        self._groupVar = groupVar
        self._groups = groups
        self._bench_matrix = bench_matrix
        self._group_assignements = group_assignements
        self._num_players = num_players
        self._num_rounds = num_rounds
        self._num_courts = num_courts
        self._solution_count = 0
        self._solution_limit = limit
        self._bestCourtDiffMax = num_rounds
        self._numPlayersWith_best = num_players


    def on_solution_callback(self):
        """Print the current solution."""
        self._solution_count += 1
        self.print_schedule()
        if self._solution_count >= self._solution_limit:
            print(f'Stop search after {self._solution_limit} solutions')
            self.StopSearch()


    def print_schedule(self):
        """Print the schedule"""

        # playersCourtCount: calculate how often (count) a player plays on each court
        playersCourtCount={}
        for court in range(self._num_courts):
            playersCourtCount[court] = []
            for player in range(self._num_players):
                courtCount=0
                for group in range(self._num_courts):
                    for round in range(self._num_rounds):
                        if self.Value(self._games[(round, court, group)]):
                            if self._group_assignements[round][group][player]:
                                courtCount=courtCount+1
                playersCourtCount[court].append(courtCount)
        
        # playersCourtDiffMax: calculate the difference between the max and min courtcount 
        # for each player 
        playersCourtDiffMax = []
        for player in range(self._num_players):
            maxCount = max(playersCourtCount[court][player] for court in range(self._num_courts))
            minCount = min(playersCourtCount[court][player] for court in range(self._num_courts))
            playersCourtDiffMax.append(maxCount-minCount)

        # keep the new solution if it is better then any previous
        # determined by max(playersCourtDiffMax) and if 
        # max(playersCourtDiffMax) is the same keep less players have 
        # the same CourtDiff 
        printit=False
        if self._bestCourtDiffMax==max(playersCourtDiffMax):
            # print some info to verify that other solutions exist
            # with same CourtDiffMax
            print(f'{max(playersCourtDiffMax)}-{playersCourtDiffMax.count(max(playersCourtDiffMax))}, ') 
            if self._numPlayersWith_best>=playersCourtDiffMax.count(max(playersCourtDiffMax)):
                self._numPlayersWith_best=playersCourtDiffMax.count(max(playersCourtDiffMax))
                printit=True
        if self._bestCourtDiffMax>max(playersCourtDiffMax):
            self._bestCourtDiffMax=max(playersCourtDiffMax)
            self._numPlayersWith_best=playersCourtDiffMax.count(max(playersCourtDiffMax))
            printit=True

        # if current solution is a better solution, then print it
        if printit:
            time_now = datetime.now().strftime("%H:%M:%S")
            print(f'{time_now} : Solution {self._solution_count}')

            # print court counts for each player
            print(f'              Players ' )    
            groupAssigned= {}
            for court in range(self._num_courts):
                groupAssigned[court] = []
                for player in range(self._num_players):
                    count=0
                    for group in range(self._num_courts):
                        for round in range(self._num_rounds):
                            v1=self.Value(self._games[(round, court, group)])
                            v2=self.Value(self._groupVar[(round, group, player)])
                            #print(court,player,group,round,v1,v2,count)
                            if v1+v2==2:
                                count=count+1
                    groupAssigned[court].append( count ) 
                # print current court counts per players
                print(f' Court   {court:4}:  {groupAssigned[court]}' )    
            print(f' MaxDiff     :  {playersCourtDiffMax}') 
            print(f' Max difference: {max(playersCourtDiffMax):2} for {self._numPlayersWith_best} players') 

            # print court and bench player assignments            
            print(' '.ljust(14), ' '.join([f'court {i+1:2}'.ljust(19) for i in range(self._num_courts)]), 'bench'.ljust(10))
            playersAssigned={}
            for round in range(self._num_rounds):
                group_ass = self._groups[round]
                for court in range(self._num_courts):
                    for group in range(self._num_courts):
                        groupMembers=group_ass[f'{group}']
                        if self.Value(self._games[(round, court, group)]):
                            playersAssigned[court] = groupMembers
                            #print(round, court, group, groupMembers)
                str_games = [f'{v}'.ljust(18) for v in playersAssigned.values()]
                str_bench = [f' {self._bench_matrix[round]}'.ljust(30)]
                print(f' Round {round+1:4}:  ', '  '.join(str_games), ' '.join(str_bench) )

    def solution_count(self):
        """Return number of solution found so far."""
        return self._solution_count


def main():
    """Entry point of the program"""
    parser = argparse.ArgumentParser(description='Compute friendly tennis schedule.')
    parser.add_argument('--players',
                        '-p',
                        default=12,
                        type=int,
                        help='number of players (default:12)')
    parser.add_argument('--rounds',
                        '-r',
                        default=6,
                        type=int,
                        help='number of rounds (default:6)')
    parser.add_argument('--courts',
                        '-c',
                        default=3,
                        type=int,
                        help='number of courts played per round (default:3)')
    parser.add_argument('--file',
                        '-f',
                        default='bench.txt',
                        type=str,
                        help='filename for list of players on bench (default:bench.txt)')
    args = vars(parser.parse_args())


    # Data.
    fname=args['file']
    num_players = args['players']
    num_rounds = args['rounds']
    num_courts = args['courts'] 
    num_players_per_court=4
    num_bench = num_players- (num_courts*num_players_per_court)
        
    print(f"players: {num_players}, rounds: {num_rounds}, courts played per round: {num_courts}, on bench: {num_bench}")
    if num_bench>0:
        min_bench=math.floor(num_rounds*num_bench/num_players)
        max_bench=math.ceil(num_rounds*num_bench/num_players)
        distance_on_bench=math.ceil(num_players/num_bench)-2
        print(f"min/max presence on bench is {min_bench} / {max_bench}")
        print(f"minimal distance on bench is {distance_on_bench}")


    # Creates the model.
    model = cp_model.CpModel()

    # Creates games variables.
    all_players = range(num_players)
    all_rounds = range(num_rounds)
    all_played_courts = range(num_courts)
    all_courts = range(num_courts+1)
    all_bench = range(num_courts+1,num_courts+1)
    benchcourt=num_courts  # last "court" is the bench

    rand_players=list(range(num_players))
    random.shuffle(rand_players)
    groupVar = {}
    duoVar = {}
    games = {}


    bench_list = []
    if num_bench>0:

        # Open the file and read the content in a list
        with open(fname, 'r') as filehandle:
            bench_list = json.load(filehandle)

    bench_matrix=[]
    count=0
    # assign players on bench for each round in the model
    for _ in all_rounds:
        bench=[]
        for _ in range(num_bench):
            bench.append(bench_list[count])
            count=count+1
        bench_matrix.append(bench)
    #print(bench_list)
    #print(bench_matrix)
    #print(num_bench)

    # define basic game matrix as a boolean var indicating when a group of players
    # is allocated (true) on a specific court in a round
    # games[(r, c, g)]: group of players 'g' play on court 'c' in round 'r'.
    for round in all_rounds:
        for court in all_played_courts:
            for group in all_played_courts:
                games[(round, court, group)] = model.NewBoolVar(f'r{round}_c{court}_g{group}')

    # constraints on game matrix

    # constraint #1) 
    # in each round, each group is assigned to exactly 1 court.
    for round in all_rounds:
        for group in all_played_courts:
            tmp_courts = []
            for court in all_played_courts:
                tmp_courts.append(games[(round, court, group)])
            model.Add(sum(tmp_courts) == 1)

    # constraint #2) 
    # in each round, each court is assigned to exactly 1 group.
    for round in all_rounds:
        for court in all_played_courts:
            tmp_groups = []
            for group in all_played_courts:
                tmp_groups.append(games[(round, court, group)])
            model.Add(sum(tmp_groups) == 1)

    # explicitly assign group of players in each round
    # based on input file information
    groups = []
    # Open the file and read the content in a list
    with open(f'groups_{fname}', 'r') as filehandle:
        groups = json.load(filehandle)

    group_assignements = [[ [0 for _ in all_players] for _ in all_played_courts] for _ in all_rounds]
    for round in all_rounds:
        group_ass = groups[round]
        for group in all_played_courts:
            groupMembers=group_ass[f'{group}']
            for member in range(num_players_per_court):
                player=groupMembers[member]-1
                group_assignements[round][group][player]=1
    #print(group_assignements)

    for round in all_rounds:
        for group in all_played_courts:
            for player in all_players:
                groupVar[(round, group, player)] = model.NewBoolVar(f'r{round}_g{group}_p{player}')
                model.Add(groupVar[(round, group, player)]== group_assignements[round][group][player])


    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 2
    # Enumerate all solutions.
    solver.parameters.enumerate_all_solutions = True
    solver.parameters.search_branching = cp_model.PORTFOLIO_SEARCH
    # AUTOMATIC_SEARCH = sat_parameters_pb2.SatParameters.AUTOMATIC_SEARCH
    # FIXED_SEARCH = sat_parameters_pb2.SatParameters.FIXED_SEARCH
    # PORTFOLIO_SEARCH = sat_parameters_pb2.SatParameters.PORTFOLIO_SEARCH
    # LP_SEARCH = sat_parameters_pb2.SatParameters.LP_SEARCH



    # Display the first five solutions.
    solution_limit = 500000
    solution_printer = PlayersPartialSolutionPrinter(games, group_assignements, groupVar, num_players,
                                                    num_rounds, num_courts,
                                                    solution_limit, groups, bench_matrix)

    # solve
    time_now = datetime.now().strftime("%H:%M:%S")
    print(f'{time_now} solving...' )

    solver.Solve(model, solution_printer)

    # Statistics.
    print('\nSolver Statistics:')
    print(f'- conflicts      : {solver.NumConflicts()}')
    print(f'- branches       : {solver.NumBranches()}')
    print(f'- wall time      : {solver.WallTime()} s')
    print(f'- solutions found: {solution_printer.solution_count()}')


if __name__ == '__main__':
    main()