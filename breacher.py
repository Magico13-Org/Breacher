import copy
import operator
import time
from typing import Tuple

class _sequence(object):
    def __init__(self, sequence, score) -> None:
        super().__init__()
        self.sequence = sequence
        self.score = score


class Breacher(object):
    def __init__(self) -> None:
        super().__init__()
        self.grid = []
        self.targets = []
        self.target_strs = []
        self.buffer_size = 0
        self.smallest_target = 0
        self.max_value = 0
        self.total_tested = 0
        self.total_solutions = 0
        self.open_sequences = {} # key is score, value is list of sequences with that score

    def load_sample_grid(self):
        with open('examples/example.csv') as f:
            for line in f:
                line = line.strip()
                if line:
                    self.grid.append(line.split())
    
    def set_grid(self, the_grid):
        '''Sets the grid to the provided value (2D array of the text values)'''
        self.grid = copy.deepcopy(the_grid)

    def set_targets(self, targets, buffer_size):
        '''Sets the target sequences, should be given in lowest to highest value'''
        self.targets = targets
        self.buffer_size = buffer_size
        self.shortest_solution = buffer_size
        self.smallest_target = buffer_size
        self.target_strs = []
        self.max_value = 0
        for i in range(len(self.targets)):
            tgt = self.targets[i]
            tgt_len = len(tgt)
            if tgt_len < self.smallest_target: self.smallest_target = tgt_len
            self.target_strs.append(''.join(str(s) for s in tgt))
            self.max_value += pow(2, i)

    def solve(self, shortest=False):
        '''Using the provided grid and targets, returns the best sequence (first) and score (second)'''
        #sanity check
        buffer = []
        score = 0.0
        remaining_grid = copy.deepcopy(self.grid)
        if self.buffer_size <= 0 or len(self.targets) == 0 or len(self.grid) == 0:
            print('Inavlid setup')
            return buffer, score

        self.total_tested = 0
        self.total_solutions = 0
        self.open_sequences = {}

        #start in the top row, alternate between rows/columns, build up the best scoring sequence (breadth first basically), to a depth equal to the buffer size
        #score goes up 0 if not a useful choice, 0.1 if it gets closer to completing a target, and 2^target position for completing a target
        buffer, score = self._solve_step(remaining_grid, buffer, 0, 0, False, 0, not shortest)
        if self.total_solutions == 0:
            print('No valid solutions! Returning best solution found.')
        return buffer, score

    def _solve_step(self, remaining, buffer, x, y, isColumn, depth, stop_on_first=False):
        '''internal function for a step in solving'''
        #x,y is the most recent choice. If isColumn then we're looking at items in the same column (same y), else in same row (same x)
        buffer = copy.deepcopy(buffer)
        remaining = copy.deepcopy(remaining)
        if not (depth == 0 and x == 0 and y == 0 and not isColumn): #skip the very first one
            #buffer.append(self.grid[x][y])
            buffer.append((x, y))

        current_value = self.get_value(buffer)
        if depth >= self.shortest_solution or current_value >= self.max_value:
            if depth < self.shortest_solution:
                self.shortest_solution = depth # if we find one that's 7 that matches all targets and our buffer is 8, stop checking for longer solutions
            self.total_tested += 1
            if current_value >= self.max_value: 
                self.total_solutions += 1
                #print(' '.join(self.positions_to_text(buffer)), buffer)
            return buffer, current_value # we currently build the buffer up after we've reached the max
            # instead we should build it up the other way, then we can short out when we hit the target(s) in less codes
        options = []
        if isColumn:
            for xG in range(len(self.grid)):
                options.append(remaining[xG][y])
        else:
            for yG in range(len(self.grid[0])):
                options.append(remaining[x][yG])
        # print(options)
        # go through the options one by one, pick the one that ups the score the most
        
        sequences = {}
        for i in range(len(options)):
            opt = options[i]
            if opt == '': continue
            new_pos = (x, i)
            if isColumn: new_pos = (i, y)
            newbuf = copy.deepcopy(buffer)
            newbuf.append(new_pos)
            score = self.get_value(newbuf)
            sequences[i] = score           

        # we now have all the possible options and their scores, pick the best scoring one
        best_sequence = None
        best_score = -1
        for kvp in sorted(sequences.items(), key=operator.itemgetter(1),reverse=True):
            i = kvp[0]
            opt = options[i]
            new_pos = (x, i)
            if isColumn: new_pos = (i, y)

            remaining[new_pos[0]][new_pos[1]] = ''
            seq, value = self._solve_step(remaining, buffer, new_pos[0], new_pos[1], not isColumn, depth+1, stop_on_first)
            remaining[new_pos[0]][new_pos[1]] = opt

            if value > best_score:
                best_score = value
                best_sequence = seq
                if value >= self.max_value:
                    if stop_on_first or len(seq) == self.smallest_target:
                        break


        #print(depth, best_sequence, best_score)
        return best_sequence, best_score

    def solve_v2(self):
        buffer = []
        score = 0.0
        remaining_grid = copy.deepcopy(self.grid)
        if self.buffer_size <= 0 or len(self.targets) == 0 or len(self.grid) == 0:
            print('Inavlid setup')
            return buffer, score

        self.total_tested = 0
        self.total_solutions = 0
        self.open_sequences = {}
        
        found = False

        while not found:
            # pick the best scoring option from the list of open sequences
            # check the new options and add them to the open list
            # repeat until a solution is found
            highest_score = 0 if not self.open_sequences else sorted(self.open_sequences.keys)[0]
            seq = self.open_sequences.pop(highest_score, [])
            if seq:
                last = seq[:-1]
            else:
                last = (0,0)
            options = self._build_options(remaining_grid, seq, last[0], last[1])
            print(options)

    def _build_options(self, remaining, buffer, x, y):
        isColumn = (len(buffer) % 2) == 1
        options = {}
        if isColumn:
            for xG in range(len(self.grid)):
                options[xG] = remaining[xG][y]
        else:
            for yG in range(len(self.grid[0])):
                options[yG] = remaining[x][yG]
        return options


    # def _solve_step_shortest2(self, remaining, buffer, x, y, isColumn, depth):
    #     '''internal function for a step in solving'''
    #     #x,y is the most recent choice. If isColumn then we're looking at items in the same column (same y), else in same row (same x)
    #     buffer = copy.deepcopy(buffer)
    #     remaining = copy.deepcopy(remaining)
    #     if not (depth == 0 and x == 0 and y == 0 and not isColumn): #skip the very first one
    #         #buffer.append(self.grid[x][y])
    #         buffer.append((x, y))

    #     options = []
    #     if isColumn:
    #         for xG in range(len(self.grid)):
    #             options.append(remaining[xG][y])
    #     else:
    #         for yG in range(len(self.grid[0])):
    #             options.append(remaining[x][yG])
        
    #     for i in range(len(options)):
    #         opt = options[i]
    #         if opt == '': continue
    #         new_pos = (x, i)
    #         if isColumn: new_pos = (i, y)
            
    #         newbuf = copy.deepcopy(buffer)
    #         newbuf.append(new_pos)

    #         score = self.get_value(newbuf)
    #         self.open_sequences.append(_sequence(newbuf, score))

    #     # we now have all the possible options and their scores, pick the best scoring one
    #     best_sequence = None
    #     best_score = -1
    #     for kvp in sorted(sequences.items(), key=operator.itemgetter(1),reverse=True):
    #         i = kvp[0]
    #         opt = options[i]
    #         new_pos = (x, i)
    #         if isColumn: new_pos = (i, y)

    #         remaining[new_pos[0]][new_pos[1]] = ''
    #         seq, value = self._solve_step_shortest(remaining, buffer, new_pos[0], new_pos[1], not isColumn, depth+1)
    #         remaining[new_pos[0]][new_pos[1]] = opt

    #         if value > best_score:
    #             best_score = value
    #             best_sequence = seq
    #             # if value >= self.max_value:
    #             #     break


    #     #print(depth, best_sequence, best_score)
    #     return best_sequence, best_score
            
    def get_value(self, positions) -> float:
        '''Gets the value of a sequence based on the current targets'''
        #doing this each time is wasteful, should find a way to do this incrementally instead of checking whole list
        #loop through the sequence, check if it's close to any targets
        #first pass ignores partials
        #lets just use strings and the in operator at first
        #could also prioritize moves that are closer together (less mouse travel)
        sequence = self.positions_to_text(positions)
        seq_str = ''.join(str(s) for s in sequence)
        total_value = 0
        for i in range(len(self.target_strs)):
            value = pow(2, i)
            tgt_str = self.target_strs[i]
            if tgt_str in seq_str: total_value += value
            else:
                #check if the start of the target exists at the end of the current sequence
                for j in range(2, len(tgt_str), 2):
                    substr = tgt_str[:j]
                    if seq_str.endswith(substr):
                        total_value += 0.01*j
        #also gets a bonus of up to 0.1 points for being under the max size
        bonus = 0.1 * (1 - (len(positions)/self.buffer_size))
        total_value += bonus
        return total_value
    
    def positions_to_text(self, positions):
        '''Convert a position sequence to the values at those positions'''
        sequence = []
        for pos in positions:
            sequence.append(self.grid[pos[0]][pos[1]])
        return sequence


if __name__ == "__main__":
    start = time.perf_counter()
    breach = Breacher()
    breach.load_sample_grid()
    breach.set_targets([
            #['BD', '1C'],
            ['1C', '55', '7A'],
            ['E9', '1C', '1C'],
            ['E9', '55', 'E9', 'E9']
        ], 8)
    # sequence, score = breach.solve()
    breach.solve_v2()
    elapsed = time.perf_counter() - start
    print('Solution:', sequence, breach.positions_to_text(sequence), score, elapsed)
    print('{0} solutions, {1} tested'.format(breach.total_solutions, breach.total_tested))
