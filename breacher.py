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
        if self.buffer_size <= 0 or len(self.targets) == 0 or len(self.grid) == 0:
            print('Inavlid setup')
            return [], 0.0

        self.total_tested = 0
        self.total_solutions = 0
        self.open_sequences = {}
        self.shortest_solution = self.buffer_size
        
        best_sequence = []
        best_score = 0.0

        searching = True

        while searching:
            # pick the best scoring option from the list of open sequences
            # check the new options and add them to the open list
            # repeat until a solution is found
            highest_score = 0 if not self.open_sequences else sorted(self.open_sequences.keys(), reverse=True)[0]
            seq = [] #if we're just starting out we have an empty sequence
            if highest_score > 0:
                sequences = self.open_sequences[highest_score] #grab the list of sequences with that score
                seq = sequences.pop(0) #grab the first sequence in the list of sequences, it's the oldest
                if not sequences: #list empty now, remove from the open_sequences
                    del self.open_sequences[highest_score]
                if not self.open_sequences:
                    searching = False #we've run out out options
            last = (0,0) #the last element in the sequence
            if seq: last = seq[-1]
            isColumn = (len(seq) % 2) == 1
            remaining_grid = self._build_remaining_grid(self.grid, seq) #empty out all the elements that have been chosen in the sequence
            options = self._build_options(remaining_grid, seq, last[0], last[1], isColumn) #get all the new options
            # print(self.positions_to_text(seq))
            for i in options: #loop over the options, get the value of the new sequence if we chose that one
                new_pos = (last[0], i)
                if isColumn: new_pos = (i, last[1])
                new_seq = seq + [new_pos]
                score = self.get_value(new_seq)
                new_seq_len = len(new_seq)
                if score > best_score:
                    best_score = score
                    best_sequence = new_seq
                if score >= self.max_value:
                    self.total_tested += 1
                    self.total_solutions += 1
                    if shortest and new_seq_len < self.shortest_solution:
                        self.shortest_solution = new_seq_len
                    elif not shortest:
                        return new_seq, score
                if new_seq_len >= self.buffer_size or new_seq_len > self.shortest_solution: #we can short out if we have already found a shorter one
                    self.total_tested += 1
                    continue #if it didn't succeed then we're out of buffer space
                if score in self.open_sequences: self.open_sequences[score].append(new_seq)
                else: self.open_sequences[score] = [new_seq] #add the new sequence and score to the open_sequences
        #if we got here then we haven't found a perfect option
        print('No valid solutions! Returning best solution found.')
        return best_sequence, best_score

    def _build_options(self, remaining, buffer, x, y, isColumn):
        options = {}
        if isColumn:
            for xG in range(len(self.grid)):
                if remaining[xG][y] != '':
                    options[xG] = remaining[xG][y]
        else:
            for yG in range(len(self.grid[0])):
                if remaining[x][yG] != '':
                    options[yG] = remaining[x][yG]
        return options

    def _build_remaining_grid(self, original_grid, seq):
        remaining = copy.deepcopy(original_grid)
        for pos in seq:
            remaining[pos[0]][pos[1]] = ''
        return remaining
            
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
            # ['7A', '1C', '1C'],
            # ['1C', 'E9', 'BD'],
            # ['1C', '1C', '1C', '55']
        ], 9)
    sequence, score = breach.solve()
    # sequence, score = breach.solve_v2()
    elapsed = time.perf_counter() - start
    print('Solution:', sequence, breach.positions_to_text(sequence), score, elapsed)
    print('{0} solutions, {1} tested'.format(breach.total_solutions, breach.total_tested))
