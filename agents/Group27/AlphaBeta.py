from random import random
from time import perf_counter
from copy import deepcopy
from BoardSupport import Coordinates

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
            print("ERROR: NO EVAL FUNCTION")


    def make_move(self, board, player, depth=2):
        """ Makes a move according to Wolve's preferences
        """

        self.node_count = 0
        start_time = perf_counter()

        choices = Coordinates.get_empty(board)
        val, move = self.alpha_beta(deepcopy(board), choices, player, depth)

        print(f"ab finish: val={val}; move={move}; nodes={self.node_count} time={perf_counter() - start_time}")

        return move

    def dfs(self, board, player, i, j, front, back):
        """ Depth First Search for win checking 
            Red top->bottom
            Blue left->right """
        # print(f"dfs: i={i}; j={j}; board={board}")

        # validate the coordinates to check
        if i < 0 or i >= self._board_size or j < 0 or j >= self._board_size or board[i][j] != player:
            return front, back

        # success if at vertical edges for Blue
        if (i == 0) and player == "B":
            front = True
        if (i == self._board_size - 1 and player == "B"):
            back = True

        # success if at horizontal edges for Red
        if j == 0 and player == "R":
            front = True
        if j == self._board_size - 1 and player == "R":
            back = True

        # update board to mark where we've been
        board[i][j] = "#"
        # iterate through checking neighbours
        for dx, dy in self.DIRECTIONS:
            # check neighbours
            next_front, next_back = self.dfs(board, player, i + dx, j + dy, front, back)
            if next_front and next_back:
                return True, True

        # no neighbours or connections to edges
        return front, back

    def check_winner(self, board):
        """ Checks if there is a connection from one side of the board to the other
            Red top->bottom
            Blue left->right
            Return 1 for Red win, -1 for Blue win, 0 for no winner """

        # iterate over top row to start dfs search
        for i in range(self._board_size):
            front, back = self.dfs(deepcopy(board), "R", i, 0, False, False)
            if board[i][0] == 'R' and front and back:
                return 1
        #  iterate over left column to start dfs search
        for j in range(self._board_size):
            front, back = self.dfs(deepcopy(board), "B", 0, j, False, False)
            if board[0][j] == 'B' and front and back:
                return -1
        return 0

    def alpha_beta(self, board, choices, player, depth, alpha=-1000.0, beta=1000.0):
        """ Using min-max with alpha beta pruning
            Red maximising
            Blue minimising
            return the move we want to make """
        # print(f"alpha beta: depth={depth}; alpha={alpha}; beta={beta}; choices={len(choices)}")
        best_move = (-1, -1)
        self.node_count += 1

        if depth == 0 or len(choices) == 0:
            win = self.check_winner(deepcopy(board))
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