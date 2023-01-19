#!/usr/bin/env python3
import argparse
from datetime import datetime
import json
import math
from operator import mod
import random
from ortools.sat.python import cp_model

"""

Scheduling of friendly games for players sharing tennis courts (doubles).
Part 2:  Assignment of players on each playing court. 

Parameters:
    number of tennis courts available
    number of players available (some players might sit on bench on some games )
    number of rounds (turn) to be played
    file containing set of players on bench on each round 
        input as {fname}
        output as groups_{fname}

Constraints:
    Every player should have a chance to play with or against every other player
    Every player should play an equal (or almost) number of rounds
    Every player should not play with the same player (partner) more than once, but he/she could
        play against him/her multiple times

Objective:
    Calculating the number of times each pair of players play on the same court,
    Minimize the difference between the max and min of this calculation.
    This way, players will play similar number of times with the same players.

"""
class TeamAllocationSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""
    def __init__(self, games, bench, duoVar, num_players, num_rounds, num_courts, limit, fname):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._games = games
        self._duoVar = duoVar
        self._bench = bench
        self._fname = fname
        self._num_players = num_players
        self._num_rounds = num_rounds
        self._num_courts = num_courts
        self._solution_count = 0
        self._solution_limit = limit
        self._best = num_rounds
        self._better = num_players*(num_players+1)/2

    def on_solution_callback(self):
        """Print the current solution."""
        self._solution_count += 1
        self.print_schedule()
        if self._solution_count >= self._solution_limit:
            print(f'Stop search after {self._solution_limit} solutions')
            self.StopSearch()

    def print_schedule(self):
        # for each pair of players, calculat number of times they play on the same court
        paircounts = [ [0 for x in range(self._num_players)] for y in range(self._num_players)]
        for p1 in range(self._num_players):
            for p2 in range(p1+1, self._num_players):
                for round in range(self._num_rounds):
                    for court in range(self._num_courts):
                        p1rc = self.Value(self._games[(p1, round, court)])
                        p2rc = self.Value(self._games[(p2, round, court)])
                        if p1rc+p2rc == 2:
                            paircounts[p1][p2]=paircounts[p1][p2]+1
        
        # and determine max and min count
        maxCount = max(paircounts[p1][p2] for p1 in range(self._num_players) for p2 in range(p1+1, self._num_players))
        minCount = min(paircounts[p1][p2] for p1 in range(self._num_players) for p2 in range(p1+1, self._num_players))

        # Minimize the difference between the max and min of this calculation.
        # This way, players will play similar number of times with the same players.
        printit=False
        sameplayers=0

        # if current solution is better or equal to previous solutions print/save it.
        if maxCount-minCount <= self._best :
            for p1 in range(self._num_players):
                for p2 in range(p1+1, self._num_players):
                    for r1 in range(self._num_rounds):
                            rn=mod(r1+1,self._num_rounds)
                            for c1 in range(self._num_courts):
                                for c2 in range(self._num_courts):
                                    p1r1c1 = self.Value(self._games[(p1, r1, c1)])
                                    p2r1c1 = self.Value(self._games[(p2, r1, c1)])
                                    p1rnc2 = self.Value(self._games[(p1, rn, c2)])
                                    p2rnc2 = self.Value(self._games[(p2, rn, c2)])
                                    if p1r1c1+p2r1c1+p1rnc2+p2rnc2 == 4:
                                        sameplayers=sameplayers+1
                                        #print(f' Players: {p1:2}-{p2:2} round:{r1:2}-{rn:2} courts:{c1:2}-{c2:2} ')

            self._best = maxCount-minCount
            if maxCount-minCount < self._best :
                printit=True
            if sameplayers <= self._better:
                printit=True
                self._better=sameplayers

        if printit:
            time_now = datetime.now().strftime("%H:%M:%S")
            print(f'Solution {self._solution_count} @ {time_now}')
            print(f'player pairs :')
            for player in range(self._num_players):
                print(paircounts[player])
            print(f'{maxCount} {minCount} {self._best}: consecutive games with same players: {self._better}')
            """Print the schedule"""
            print(' '.ljust(14), ' '.join([f'court {i+1:2}'.ljust(19) for i in range(self._num_courts)]), 'bench'.ljust(10))
            
            for round in range(self._num_rounds):
                games = {}
                bench = {}
                for court in range(self._num_courts):
                    games[court] = []
                    pair=court*2
                    for player in range(self._num_players):
                        if self.Value(self._duoVar[(player, round, pair)]):
                            #print(f'  player {player} plays court {court}')
                            games[court].append(player+1)
                    #games[court].append("vs")
                    for player in range(self._num_players):
                        if self.Value(self._duoVar[(player, round, pair+1)]):
                            #print(f'  player {player} plays court {court}')
                            games[court].append(player+1)
                str_games = [f'{v}'.ljust(18) for v in games.values()]
                bench = []
                for player in range(self._num_players):
                    if self.Value(self._games[(player, round, self._num_courts)]):
                        #print(f'  player {player} plays court {self._num_courts}')
                        bench.append(player+1)
                str_bench = [f' {bench}'.ljust(30)]
                print(f' Round {round+1:4}:  ', '  '.join(str_games), ' '.join(str_bench) )
                self.write_bench(self._fname)

    def solution_count(self):
        """Return number of solution found so far."""
        return self._solution_count

    def write_bench(self,fname):
        """Print the tournament schedule"""
        groups = []
        for round in range(self._num_rounds):
            games = {}
            for court in range(self._num_courts):
                games[court] = []
                pair=court*2
                for player in range(self._num_players):
                    if self.Value(self._duoVar[(player, round, pair)]):
                        games[court].append(player+1)
                for player in range(self._num_players):
                    if self.Value(self._duoVar[(player, round, pair+1)]):
                        games[court].append(player+1)
            groups.append(games)

        with open(fname, 'w') as filehandle: 
            json.dump(groups, filehandle)

def main():
    # validate input and prepare data
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
    benchVar = {}
    duoVar = {}
    games = {}

    # define basic game matrix as a boolean var indicating when a player is allocated (true)
    # on a specific court in a round
    # games[(p, t, c)]: player 'p' play on round 't' on court 'c'.
    for player in all_players:
        for round in all_rounds:
            for court in all_courts:
                games[(player, round, court)] = model.NewBoolVar(f'p{player}_t{round}_c{court}')

    # constraints on game matrix

    # constraint #1) 
    # First num_courts on each round is assigned to exactly num_players_per_court players.
    for round in all_rounds:
        for court in all_played_courts:
            tmp_players = []
            for player in all_players:
                tmp_players.append(games[(player, round, court)])
            model.Add(sum(tmp_players) == num_players_per_court)

    # constraint #2) 
    # bench roster (last "court" in matrix) per round must be equal to num_bench players
    if 1:
        for round in all_rounds:
            for court in all_bench:
                tmp_players = []
                for player in all_players:
                    tmp_players.append(games[(player, round, court)])
                model.Add(sum(tmp_players) == num_bench)

    # constraint #3) 
    # Each player must be placed in one playing court or on the bench per round.
    for player in all_players:
        for round in all_rounds:
            model.AddExactlyOne(games[(player, round, court)] for court in all_courts)

    # constraint #4) 
    # explicitly assign players on bench if number of players on bench (num_bench) is > 0
    if num_bench>0:
        bench_list = []
        # Open the file and read the content in a list
        with open(fname, 'r') as filehandle:
            bench_list = json.load(filehandle)

        count=0
        bench_assignements=[ [ 0 for t in all_rounds] for p in all_players ]
        bench_matrix=[]
        # assign players on bench for each round in the model
        for round in all_rounds:
            bench=[]
            for _ in range(num_bench):
                bench.append(bench_list[count])
                bench_assignements[bench_list[count]-1][round]=1
                model.Add(games[(bench_list[count]-1, round, benchcourt)]== 1)
                count=count+1
            bench_matrix.append(bench)

        # assign players on bench for each round in the model by
        # defining bench variable and match assignement on games matrice
        for player in all_players:
            for round in all_rounds:
                benchVar[(player, round)] = model.NewBoolVar(f'p{player}_t{round}')
                model.Add(benchVar[(player, round)]== games[(player, round, benchcourt)]  )
        
    # constraint #5)
    # every pair of players should play in the same court (with or against eachother) at least once
    if 1:
        for p1 in all_players:
            for p2 in range(p1+1, num_players):
                tmp = []
                for round in all_rounds:
                    for court in all_played_courts:
                        b_var = model.NewBoolVar(f'b_p{p1}_p{p2}_r{round}_c{court}')
                        model.Add(games[(p1, round, court)] + games[(p2, round, court)] \
                            ==  2).OnlyEnforceIf(b_var)
                        model.Add(games[(p1, round, court)] + games[(p2, round, court)] \
                            !=  2).OnlyEnforceIf(b_var.Not())
                        tmp.append(b_var)
                model.Add(sum(tmp) >0)

    # define each pair of partners (duo) for each court and ensure they refer to a court in the game matrice
    if 1:
        for player in all_players:
            for round in all_rounds:
                for court in all_played_courts:
                    pair=court*2
                    duoVar[(player, round, pair)]   = model.NewBoolVar(f'p{player}_t{round}_d{pair}')
                    duoVar[(player, round, pair+1)] = model.NewBoolVar(f'p{player}_t{round}_d{pair+1}')
                    model.Add(duoVar[(player, round, pair)] + duoVar[(player, round, pair+1)] \
                        == games[(player, round, court)] )
 
    # constraint #6)
    # every pair of partners should have exactly 2 players assigned
    if 1:
        for round in all_rounds:
            for court in all_played_courts:
                pair=court*2
                tmp_pair1 = []
                tmp_pair2 = []
                for player in all_players:
                    tmp_pair1.append(duoVar[(player, round, pair)])
                    tmp_pair2.append(duoVar[(player, round, pair+1)])
                model.Add(sum(tmp_pair1) == 2)
                model.Add(sum(tmp_pair2) == 2)

    # constraint #7)
    # every pair of partners should be unique 
    # we want players to play with (partners) different people, never with the same
    if 1:
        for p1 in all_players:
            for p2 in range(p1+1, num_players):
                tmp = []
                for round in all_rounds:
                    for court in all_played_courts:
                        pair=court*2
                        b_var = model.NewBoolVar(f'b_p{p1}_p{p2}_t{round}_d{pair}')
                        model.Add(duoVar[(p1, round, pair)]+ duoVar[(p2, round, pair)] \
                            ==  2).OnlyEnforceIf(b_var)
                        model.Add(duoVar[(p1, round, pair)]+ duoVar[(p2, round, pair)] \
                            !=  2).OnlyEnforceIf(b_var.Not())
                        tmp.append(b_var)
                        b_var = model.NewBoolVar(f'b_p{p1}_p{p2}_t{round}_d{pair+1}')
                        model.Add(duoVar[(p1, round, pair+1)]+ duoVar[(p2, round, pair+1)] \
                            ==  2).OnlyEnforceIf(b_var)
                        model.Add(duoVar[(p1, round, pair+1)]+ duoVar[(p2, round, pair+1)] \
                            !=  2).OnlyEnforceIf(b_var.Not())
                        tmp.append(b_var)
                model.Add(sum(tmp) < 2)

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 2
    # Enumerate all solutions.
    solver.parameters.enumerate_all_solutions = True
    solver.parameters.search_branching = cp_model.PORTFOLIO_SEARCH

    # Display the first five solutions.
    solution_limit = 50000
    solution_printer = TeamAllocationSolutionPrinter(games, benchVar, duoVar, num_players,
                                                    num_rounds, num_courts,
                                                    solution_limit, f'groups_{fname}')

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