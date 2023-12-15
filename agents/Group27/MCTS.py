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

        # # set initial 50% win rate to prevent unvisite nodes being discarded
        # self.wins, self.visits = 1, 2
        self.wins, self.visits = 0, 0


    # get recommended exploration constant from lectures
    def ucb_score(self, exploration_constant=1.5):
        if self.visits == 0:
            return float('inf')

        exploitation = self.wins / self.visits
        exploration = exploration_constant * math.sqrt(math.log(self.parent.visits + 1) / self.visits)
        return exploitation + exploration

    def update(self, is_win):
        self.visits += 1
        if is_win: 
            self.wins += 1

    def is_leaf(self):
        return len(self.children) == 0

    def has_parent(self):
        return self.parent is not None
    
    @staticmethod
    def tree_policy_child(node):
        """ Select best child of given node, random if all children equal otherwise always front indexed """

        best_children = []
        best_score = -float('inf')

        for child in node.children:
            score = child.ucb_score()
            if score > best_score:
                best_score = score
                best_children = [child]
            if score == best_score:
                best_children.append(child)
        if len(best_children) == 0:
            print("tree_policy_child NO CHILDREN, AT TERMINAL")
        return random.choice(best_children)

class MCTS:

    def __init__(self, board_size):
        self.board_size = board_size
    
    def selection(self, board, n):
        """ Iterative selection, updates board with given node """
        while not n.is_leaf():
            n = Node.tree_policy_child(n)
            board[n.move[0]][n.move[1]] = n.player
        return n

    def expansion(self, board, n):
        if BoardSupport.check_winner(board) == 0:
            empty = BoardSupport.get_empty(board)
            opp_player = BoardSupport.opp_player(n.player)

            # for each empty board create node as child
            # add to parent n
            # n.wins += len(empty)
            # n.visits += len(empty) * 2
            for move in empty:
                new_child = Node(move, opp_player, n, n.layer + 1)
                n.children.append(new_child)
        # else:
        #     print("REACHED TERMINAL")

    def simulate_move(self, board, moves, player):
        """ Randomise moves and play all in new order then check winner """

        # catch if no moves sent
        if len(moves) == 0:
            print("WORSE NO MOVES")
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


    def simulation(self, board, n):
        """ Perform a simulation safely copying all necessary objects"""
        
        # copy for safe simulation
        sim_board = deepcopy(board)
        sim_player = BoardSupport.opp_player(n.player)

        # get moves and catch if no moves left
        sim_moves = BoardSupport.get_empty(sim_board)
        if len(sim_moves) == 0:
            print("SIM MOVE == 0")
            return BoardSupport.check_winner(board)
        return self.simulate_move(sim_board, sim_moves, sim_player)

    def backpropagation(self, is_win, n):
        while n.has_parent(): 
                n.update(is_win)
                n = n.parent

    def best_move(self):
        best_wins = 0
        best_child = None
        for child in self.root_node.children:
            if child.wins > best_wins:
                best_wins = child.wins
                best_child = child
                
        print(f"best: wins={best_child.wins}/{best_child.visits}; win_rate={best_child.wins/best_child.visits}; move={best_child.move}; iterations={self.iterations}")
        # self.root_node.children = [best_child]
        return best_child.move
    
    def make_move(self, board, player, max_time=5):
        safe_board = deepcopy(board)
        start_time = perf_counter()
        self.iterations = 0

        self.root_node = Node(None, None, None, 0)
        self.expansion(safe_board, self.root_node)
        while ((perf_counter() - start_time)) < max_time:
            pre_time = perf_counter()
            self.iterations += 1
            # print(f"i={iterations}")
            n, b = self.root_node, deepcopy(safe_board)

            copy_time = perf_counter()
            # print(f"\nCopy Time: {(copy_time - pre_time):.8f}")
            # print(f"Root {len(n.children)}; Layer={n.layer}")
            # print(f"Board: {b}")

            # select leaf

            n = self.selection(b, n)
            selection_time = perf_counter()
            # print(f"Selection Time: {(selection_time - copy_time):.8f}")
            # print(f"Selection {len(n.children)}; Layer={n.layer}")
            # print(f"Board: {b}")

            # expand
            self.expansion(b, n)
            expansion_time = perf_counter()
            # print(f"Expansion Time: {(expansion_time - selection_time):.8f}")
            # print(f"Expansion {len(n.children)}; Layer={n.layer}")
            # print(f"Board: {b}")

            # reselect after expansion
            n = self.selection(b, n)
            selection_again_time = perf_counter()
            # print(f"Selection2 Time: {(selection_again_time - expansion_time):.8f}")
            
            # simulate
            end_state = self.simulation(b, n)

            sim_time = perf_counter()
            # print(f"Simulation Time: {(sim_time - selection_again_time):.8f}")

            # check if end state is win
            is_win = BoardSupport.evaluate_is_win(end_state, player)

            # propagate
            self.backpropagation(is_win, n)
            prop_time = perf_counter()
            # print(f"Simulation Time: {(prop_time - sim_time):.8f}")
        return self.best_move()

if __name__ == "__main__":
    # Initialize MCTS with time and iteration limits
    mcts = MCTS(11)

    # # test simulation
    # board = BoardSupport.create_board(11)
    # empty = BoardSupport.get_empty(board)
    # player = "R"
    # start_time = perf_counter()
    # MCTS.simulation(board, empty, player)
    # print(f"simulation time = {perf_counter() - start_time}") 
    # BoardSupport.check_winner(board)

    board_size = 11
    board = BoardSupport.create_board(board_size)
    player = "R"
    best_move = MCTS.make_move(board, player)
    print("Best move:", best_move)

