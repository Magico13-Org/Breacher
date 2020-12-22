import copy

class Breacher(object):
    def __init__(self) -> None:
        super().__init__()
        self.grid = []
        self.targets = []
        self.target_strs = []
        self.buffer_size = 0
        self.max_value = 0

    def load_sample_grid(self):
        with open('example.csv') as f:
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
        self.target_strs = []
        self.max_value = 0
        for i in range(len(self.targets)):
            tgt = self.targets[i]
            self.target_strs.append(' '.join(str(s) for s in tgt))
            self.max_value += pow(2, i)

    def solve(self):
        '''Using the provided grid and targets, returns the best sequence (first) and score (second)'''
        #sanity check
        buffer = []
        score = 0
        remaining_grid = copy.deepcopy(self.grid)
        if self.buffer_size <= 0 or len(self.targets) == 0 or len(self.grid) == 0:
            print('Inavlid setup')
            return buffer, score

        #start in the top row, alternate between rows/columns, build up the best scoring sequence (breadth first basically), to a depth equal to the buffer size
        #score goes up 0 if not a useful choice, 0.1 if it gets closer to completing a target, and 2^target position for completing a target
        buffer, score = self._solve_step(remaining_grid, buffer, 0, 0, False, 0)
        return buffer, score

    def _solve_step(self, remaining, buffer, x, y, isColumn, depth):
        '''internal function for a step in solving'''
        #x,y is the most recent choice. If isColumn then we're looking at items in the same column (same y), else in same row (same x)
        buffer = copy.deepcopy(buffer)
        remaining = copy.deepcopy(remaining)
        if not (depth == 0 and x == 0 and y == 0 and not isColumn): #skip the very first one
            #buffer.append(self.grid[x][y])
            buffer.append((x, y))
        if depth >= self.buffer_size: 
            return buffer, self.get_value(buffer)
        options = []
        if isColumn:
            for xG in range(len(self.grid)):
                options.append(remaining[xG][y])
        else:
            for yG in range(len(self.grid[0])):
                options.append(remaining[x][yG])
        # print(options)
        # go through the options one by one
        best_sequence = None
        best_score = -1
        for i in range(len(options)):
            opt = options[i]
            if opt == '': continue
            value = 0
            seq = None
            if isColumn:
                remaining[i][y] = ''
                seq, value = self._solve_step(remaining, buffer, i, y, not isColumn, depth+1)
                remaining[i][y] = opt
            else:
                remaining[x][i] = ''
                seq, value = self._solve_step(remaining, buffer, x, i, not isColumn, depth+1)
                remaining[x][i] = opt
            if value > best_score:
                best_score = value
                best_sequence = seq
                if value == self.max_value:
                    break
        #print(depth, best_sequence, best_score)
        return best_sequence, best_score
            
    def get_value(self, positions):
        '''Gets the value of a sequence based on the current targets'''
        #doing this each time is wasteful, should find a way to do this incrementally instead of checking whole list
        #loop through the sequence, check if it's close to any targets
        #first pass ignores partials
        #lets just use strings and the in operator at first
        sequence = self.positions_to_text(positions)
        seq_str = ' '.join(str(s) for s in sequence)
        total_value = 0
        for i in range(len(self.target_strs)):
            value = pow(2, i)
            tgt_str = self.target_strs[i]
            if tgt_str in seq_str: total_value += value
        return total_value
    
    def positions_to_text(self, positions):
        '''Convert a position sequence to the values at those positions'''
        sequence = []
        for pos in positions:
            sequence.append(self.grid[pos[0]][pos[1]])
        return sequence


if __name__ == "__main__":
    breach = Breacher()
    breach.load_sample_grid()
    breach.set_targets([
            ['BD', 'BD'],
            ['1C', '1C', 'BD'],
            ['BD', 'BD', '1C', '55']
        ], 8)
    sequence, score = breach.solve()
    print('Best option:', sequence, breach.positions_to_text(sequence), score)
    
