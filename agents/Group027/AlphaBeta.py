from random import random
from time import perf_counter
from copy import deepcopy
from BoardSupport import BoardSupport

class AlphaBeta():
    """ This class contains the functions for Min Max Alpha Beta Pruning
        using DFS for checking win conditions
    """

    DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1), (-1, 1), (1, -1)]

    def __init__(self, board_size=11, eval_func=1):
        self._board_size = board_size
        if eval_func == 0:
            self.evaluate_board = self.flat_board_evaluation
        elif eval_func == 1:
            self.evaluate_board = self.random_board_evaluation
        else:
            #print("ERROR: NO EVAL FUNCTION")
            pass


    def make_move(self, board, player, depth=2):
        """ Makes a move according to Wolve's preferences
        """

        self.node_count = 0
        start_time = perf_counter()

        choices = BoardSupport.get_empty(board)
        val, move = self.alpha_beta(deepcopy(board), choices, player, depth)

        #print(f"ab finish: val={val}; move={move}; nodes={self.node_count} time={perf_counter() - start_time}")

        return move

    

    def alpha_beta(self, board, choices, player, depth, alpha=-1000.0, beta=1000.0):
        """ Using min-max with alpha beta pruning
            Red maximising
            Blue minimising
            return the move we want to make """
        # print(f"alpha beta: depth={depth}; alpha={alpha}; beta={beta}; choices={len(choices)}")
        best_move = (-1, -1)
        self.node_count += 1

        if depth == 0 or len(choices) == 0:
            win = BoardSupport.check_winner(deepcopy(board))
            if win == 0:
                return self.evaluate_board(board, player), best_move
            return win, best_move

        # maximising
        if player == "R":
            best_val = -10000
            for i, choice in enumerate(choices):
                sim_board = deepcopy(board)
                sim_board[choice[0]][choice[1]] = player
                sim_choices = deepcopy(choices)
                move = sim_choices.pop(i)
                val, next_move = self.alpha_beta(sim_board, sim_choices, "B", depth-1, alpha, beta)
                if val > best_val:
                    best_move = move
                    best_val = val
                    alpha = val
                if alpha >= beta:
                    break
            return best_val, best_move

        # minimising
        else:
            best_val = 10000
            for i, choice in enumerate(choices):
                sim_board = deepcopy(board)
                sim_board[choice[0]][choice[1]] = player
                sim_choices = deepcopy(choices)
                move = sim_choices.pop(i)
                val, next_move  = self.alpha_beta(sim_board, sim_choices, "R", depth-1, alpha, beta)
                if val < best_val:
                    best_move = move
                    best_val = val
                    beta = val
                if alpha >= beta:
                    break
            return best_val, best_move

    def flat_board_evaluation(self, board, player):
        """ return value of current board according to player as float """
        return 0.5
        
    def random_board_evaluation(self, board, player):
        """ return value of current board according to player as float """
        return random()


if (__name__ == "__main__"):
    print("AlphaBeta.py has no main")