import random
import math
from copy import deepcopy
from time import perf_counter
from BoardSupport import BoardSupport
import sys

class Node:
    """ Node data structure is for the tree in the MCTS implementation
        No board data should be tied to the node itself """

    def __init__(self, move, player, parent, layer): 
        # move is from parent to node
        self.move, self.player, self.parent, self.layer = move, player, parent, layer
        self.children = []

        # set unvistied
        self.wins, self.visits = 0, 0


    # calculate upper bound score from visit and wins
    def ucb_score(self, exploration_constant=1.5):
        if self.visits == 0:
            return float('inf')
        # current win rate
        exploitation = self.wins / self.visits
        exploration = exploration_constant * math.sqrt(math.log(self.parent.visits + 1) / self.visits)
        return exploitation + exploration

    # update node values according to win
    def update(self, is_win):
        self.visits += 1
        if is_win: 
            self.wins += 1

    # check if any children, is leaf if none
    def is_leaf(self):
        return len(self.children) == 0

    # check if node has a parent
    def has_parent(self):
        return self.parent is not None
    
    @staticmethod
    def tree_policy_child(node):
        """ Select best child of given node, random if all children equal otherwise always front indexed """

        best_children = []
        best_score = -float('inf')

        # iterate through children
        for child in node.children:
            # calculate ucb score
            score = child.ucb_score()
            # update best
            if score > best_score:
                best_score = score
                best_children = [child]
            if score == best_score:
                best_children.append(child)
        # if no best found, choose first
        if len(best_children) == 0:
            node.children[0]
        # randomly choose from equivalently good children
        return random.choice(best_children)

class MCTS:
    """ Monte Carlo Tree Search Implementation"""

    def __init__(self, board_size):
        self.board_size = board_size
    
    # select best child iteratively until at leaf
    def selection(self, board, n):
        """ Iterative selection, updates board with given node """
        while not n.is_leaf():
            n = Node.tree_policy_child(n)
            board[n.move[0]][n.move[1]] = n.player
        return n

    # expand given node n with all possible moves from node
    def expansion(self, board, n):
        if BoardSupport.check_winner(board) == 0:
            empty = BoardSupport.get_empty(board)
            opp_player = BoardSupport.opp_player(n.player)

            for move in empty:
                new_child = Node(move, opp_player, n, n.layer + 1)
                n.children.append(new_child)

    # run simulation of given board and moves for speed
    def simulate_move(self, board, moves, player):
        """ Randomise moves and play all in new order then check winner """

        # catch if no moves sent
        if len(moves) == 0:
            moves = BoardSupport.get_empty(board)
        
        # shuffle moves
        random.shuffle(moves)
        opp_player = BoardSupport.opp_player(player)

        for i, move in enumerate(moves):
            if i % 2 == 0:
                board[move[0]][move[1]] = player
            else:
                board[move[0]][move[1]] = opp_player
        win_state = BoardSupport.check_winner(board)
        return win_state

    # run a simulation on node n
    def simulation(self, board, n):
        """ Perform a simulation safely copying all necessary objects"""
        
        # copy for safe simulation
        sim_board = deepcopy(board)
        sim_player = BoardSupport.opp_player(n.player)

        # get moves and catch if no moves left
        sim_moves = BoardSupport.get_empty(sim_board)
        if len(sim_moves) == 0:
            return BoardSupport.check_winner(board)
        return self.simulate_move(sim_board, sim_moves, sim_player)

    # backpropogate result of simulation through node structure
    def backpropagation(self, is_win, n):
        while n.has_parent(): 
                n.update(is_win)
                n = n.parent

    # select best move from root nodes children
    # choose most winning node
    def best_move(self):
        best_wins = 0
        best_child = None
        for child in self.root_node.children:
            if child.wins > best_wins:
                best_wins = child.wins
                best_child = child
        return best_child.move
    
    # create new MCTS
    def make_move(self, board, player, max_time=5):
        safe_board = deepcopy(board)
        start_time = perf_counter()
        self.iterations = 0

        self.root_node = Node(None, None, None, 0)
        self.expansion(safe_board, self.root_node)
        while ((perf_counter() - start_time)) < max_time:
            self.iterations += 1
            # copy for safe usage
            n, b = self.root_node, deepcopy(safe_board)

            # initial selection
            n = self.selection(b, n)

            # expand
            self.expansion(b, n)

            # reselect after expansion
            n = self.selection(b, n)
            # simulate
            end_state = self.simulation(b, n)

            # check if end state is win
            is_win = BoardSupport.evaluate_is_win(end_state, player)

            # propagate
            self.backpropagation(is_win, n)
        # select best move from node tree
        return self.best_move()

if __name__ == "__main__":
    # Initialize MCTS with time and iteration limits
    mcts = MCTS(11)

    board_size = 11
    board = BoardSupport.create_board(board_size)
    player = "R"
    best_move = MCTS.make_move(board, player)
    print("Best move:", best_move)

