#!/usr/bin/env python3
"""Example of a simple player scheduling problem."""
import argparse
from datetime import datetime
import json
import math
from operator import mod
from ortools.sat.python import cp_model


"""

Scheduling of friendly games for players sharing tennis courts (double games).
Part 1)  Assignment of players on bench when they are not playing

Parameters:
    number of tennis courts available
    number of players available (some players might sit on bench on some games )
    number of rounds (turn) to be played    
    file name used at output and contains set of players on bench on each round

Constraints:
    1) bench roster per round must be equal to num_bench players
    2) Each player must sit on bench between min and max number of times
    3) Each player must play a minimal number of games before sitting on bench again

Objective:
    Minimize the number of recurring pair of players on bench at the same time
       ideally, every pair of players should not be on bench at the same time more then once 

"""

class PlayersPartialSolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""
    def __init__(self, bench, num_players, num_rounds, limit, fname):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self._bench = bench
        self._fname = fname
        self._num_players = num_players
        self._num_rounds = num_rounds
        self._solution_count = 0
        self._solution_limit = limit

    def on_solution_callback(self):
        """Print the current solution."""
        self._solution_count += 1
        print(f'Solution {self._solution_count}')
        self.print_schedule()
        self.print_player_stat()
        self.write_bench(self._fname)
        if self._solution_count >= self._solution_limit:
            print(f'Stop search after {self._solution_limit} solutions')
            self.StopSearch()

    def print_schedule(self):
        """Print the bench schedule"""
        print(' '.ljust(11), ' On bench')
        for round in range(self._num_rounds):
            bench = []
            for player in range(self._num_players):
                if self.Value(self._bench[(player, round)]):
                    bench.append(player+1)
            print(f' round {round:4}:   {bench}' )

    def write_bench(self,fname):
        """Print the tournament schedule"""
        bench = []
        for round in range(self._num_rounds):
            for player in range(self._num_players):
                if self.Value(self._bench[(player, round)]):
                    bench.append(player+1)

        with open(fname, 'w') as filehandle: 
            json.dump(bench, filehandle)

    def print_player_stat(self):
        sameplayers=0
        for p1 in range(self._num_players):
            for p2 in range(p1+1, self._num_players):
                for r1 in range(self._num_rounds):
                    for r2 in range(r1+1,self._num_rounds):
                        p1r1 = self.Value(self._bench[(p1, r1)])
                        p2r1 = self.Value(self._bench[(p2, r1)])
                        p1r2 = self.Value(self._bench[(p1, r2)])
                        p2r2 = self.Value(self._bench[(p2, r2)])
                        if p1r1+p2r1+p1r2+p2r2 == 4:
                            sameplayers=sameplayers+1
        time_now = datetime.now().strftime("%H:%M:%S")
        print(f'{time_now} : bench with same players: {sameplayers}')

        if 0: # set to 1 if you want more stats information
            for p1 in range(self._num_players):
                for tr in range(self._num_rounds):
                    p1r1 = self.Value(self._bench[(p1, r1)])
                    for r2 in range(self._num_rounds-1):
                        rn=mod(r1+1+r2,self._num_rounds)
                        p1rn = self.Value(self._bench[(p1, rn)])
                        if p1r1==1 and p1rn==1:
                            print(f' Players {p1:2}: round:{r1}-{rn} numconsec {abs(rn-r1)} ')
    
    def solution_count(self):
        """Return number of solution found so far."""
        return self._solution_count

def main():
    # validate input and prepare data
    parser = argparse.ArgumentParser(description='Compute tournament schedule.')
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
    num_players = args['players']
    num_rounds = args['rounds']
    num_courts = args['courts'] 
    fname=args['file']
    num_players_per_court=4
    num_bench = num_players- (num_courts*num_players_per_court)
    print(f"players: {num_players}, rounds: {num_rounds}, courts played per round: {num_courts}, players on bench: {num_bench}")
    if num_bench==0:
        print(f"no player on bench...exiting")
        exit

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
   
    # define basic bench matrix as a boolean var indicating when a player is allocated (true)
    # on the bench in a round
    # bench[(p, r)]: player 'p' play on round 'r'.
    bench = {}
    for player in all_players:
        for round in all_rounds:
            bench[(player, round)] = model.NewBoolVar(f'p{player}_t{round}')

    # constraints on bench matrix

    # constraint #1) 
    # bench roster per round must be equal to num_bench players
    for round in all_rounds:
        tmp_players = []
        for player in all_players:
            tmp_players.append(bench[(player, round)])
        model.Add(sum(tmp_players) == num_bench)

    # constraint #2)
    if 1:
        # Each player must sit on bench between min and max number of times
        for p1 in all_players:
            tmp = []
            for t1 in all_rounds:
                b_var = model.NewBoolVar(f'b_p{p1}_t{t1}_bench')
                model.Add(bench[(p1, t1)] == 1).OnlyEnforceIf(b_var)
                model.Add(bench[(p1, t1)] != 1).OnlyEnforceIf(b_var.Not())
                tmp.append(b_var)
            model.Add(sum(tmp) >= min_bench)
            model.Add(sum(tmp) <= max_bench)

    # constraint #3)
    if 1:
        # Each player must play a minimal number of games before sitting again on bench.
        # The distance between 2 bench presence must be at least "minimum distance_on_bench"
        # verified by ensuring that a player is not (sum=0) on bench during "distance_on_bench" rounds
        for p1 in all_players:
            tmp = []
            for t1 in all_rounds:
                for t2 in range(t1+1,t1+1+distance_on_bench):
                    tn=mod(t2,num_rounds)
                    #print('5-- ', p1, t1, tn)
                    b_var = model.NewBoolVar(f'b_p{p1}_t{t1}_t{tn}_bench')
                    model.Add(bench[(p1, t1)] + bench[(p1, tn)] \
                        ==  2).OnlyEnforceIf(b_var)
                    model.Add(bench[(p1, t1)] + bench[(p1, tn)] \
                        !=  2).OnlyEnforceIf(b_var.Not())
                    tmp.append(b_var)
            # ensure that each player is not on bench during "distance_on_bench" rounds
            # --> sum must be 0
            model.Add(sum(tmp) ==0)

    # objective #1)
    if 1:
        # minimize the number of recurring pair of players on bench at the same time
        # ideally, 2 players should not be on bench at the same time more then once 
        tmp = []
        for p1 in all_players:
            for p2 in range(p1+1, num_players):
                for t1 in all_rounds:
                    for t2 in range(t1+1,num_rounds):
                        b_var = model.NewBoolVar(f'b_p{p1}_p{p2}_t{t1}_t{t2}')
                        model.Add(bench[(p1, t1)] + bench[(p2, t1)] \
                            + bench[(p1, t2)] + bench[(p2, t2)] ==  4).OnlyEnforceIf(b_var)
                        model.Add(bench[(p1, t1)] + bench[(p2, t1)] \
                            + bench[(p1, t2)] + bench[(p2, t2)] !=  4).OnlyEnforceIf(b_var.Not())
                        tmp.append(b_var)
        model.Minimize(sum(tmp))

    # Creates the solver and solve.
    solver = cp_model.CpSolver()
    solver.parameters.linearization_level = 2
    # Enumerate all solutions.
    solver.parameters.enumerate_all_solutions = True
    solver.parameters.search_branching = cp_model.PORTFOLIO_SEARCH

    # Display the first five solutions.
    solution_limit = 50
    solution_printer = PlayersPartialSolutionPrinter(bench, num_players,
                                                    num_rounds,
                                                    solution_limit, fname)

    # solve
    solver.Solve(model, solution_printer)

    # Statistics.
    print('\nSolver Statistics:')
    print(f'- conflicts      : {solver.NumConflicts()}')
    print(f'- branches       : {solver.NumBranches()}')
    print(f'- wall time      : {solver.WallTime()} s')
    print(f'- solutions found: {solution_printer.solution_count()}')

if __name__ == '__main__':
    main()