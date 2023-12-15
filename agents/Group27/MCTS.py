import random
import math
from copy import deepcopy
from time import perf_counter
from BoardSupport import BoardSupport

class Node:

    def __init__(self, move, player, parent, layer): 
        # move is from parent to node
        self.move, self.player, self.parent, self.layer= move, player, parent, layer
        self.children = []

        # set initial 50% win rate to prevent unvisite nodes being discarded
        self.wins, self.visits = 1, 2

    # get recommended exploration constant from lectures
    def ucb_score(self, exploration_constant=1.5):
        if self.visits == 0:
            return float('inf')

        exploitation = self.wins / self.visits
        exploration = exploration_constant * math.sqrt(math.log(self.parent.visits) / self.visits)
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
    def terminal(board):
        return (BoardSupport.check_winner(board) != 0)
    
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

    @staticmethod
    def best_move(node):
        best_wins = 0
        best_move = (-1, -1)
        best_visits = 0
        for child in node.children:
            if child.wins > best_wins:
                best_wins = child.wins
                best_move = child.move
                best_visits = child.visits
        print(f"best: wins={best_wins}; win_rate={best_wins/best_visits}; move={best_move}")
        return best_move

class MCTS:

    def __init__(self, max_time=5, max_iterations=1000):
        self.max_time = max_time
        self.max_iterations = max_iterations
        self.root_node = None
    
    @staticmethod
    def selection(board, n):
        """ Recursive selection, updates board with given node """
        if n.is_leaf():
            return n
        
        n = Node.tree_policy_child(n)
        board[n.move[0]][n.move[1]] = n.player
        return MCTS.selection(board, n)

    @staticmethod
    def expansion(board, n):
        if not Node.terminal(board):
            empty = BoardSupport.get_empty(board)
            opp_player = BoardSupport.opp_player(n.player)

            # for each empty board create node as child
            # add to parent n
            n.wins += len(empty)
            n.visits += len(empty) * 2
            for move in empty:
                new_child = Node(move, opp_player, n, n.layer + 1)
                n.children.append(new_child)

    @staticmethod
    def simulate_move(board, moves, player):
        """ Recursively runs a simulation move. Pass moves and board for speed, must be deep copied before call """

        # catch if no moves sent
        if len(moves) == 0:
            moves = BoardSupport.get_empty(board)
        
        # choose random move
        move = random.choice(moves)
        # print(f"sim move: {move}")
        board[move[0]][move[1]] = player
        moves.remove(move)

        win_state = BoardSupport.check_winner(board)
        if win_state != 0:
            # print("Final Board")
            # for j, row in enumerate(board):
            #     for i in range(j):
            #         print("  ", end="")
            #     print(row)
            # print(f"Win State = {win_state}")
            return win_state
        return MCTS.simulate_move(board, moves, BoardSupport.opp_player(player))

    @staticmethod
    def simulation(board, n):
        """ Perform a simulation safely copying all necessary objects"""
        
        # copy for safe simulation
        sim_board = deepcopy(board)
        sim_player = BoardSupport.opp_player(n.player)

        # get moves and catch if terminal node
        sim_moves = BoardSupport.get_empty(sim_board)
        if len(sim_moves) == 0:
            return BoardSupport.check_winner(board)
        return MCTS.simulate_move(sim_board, sim_moves, sim_player)
    
    @staticmethod
    def backpropagation(is_win, n):
        while n.has_parent(): 
                n.update(is_win)
                n = n.parent

    @staticmethod
    def make_move(board, player, max_time=2000, max_iterations=500):
        start_time = perf_counter()
        root_node = Node(None, None, None, 0)
        MCTS.expansion(board, root_node)
        iterations = 0
        # print(f"time={perf_counter() - start_time}; iter={iterations}")
        # print(f"time_flag={(max_time < int(perf_counter() - start_time))}")
        # print(f"iter_flag={iterations < max_iterations}")
        # print(f"iter={iterations}; max_iter={max_iterations}")
        while ((perf_counter() - start_time)) < max_time and iterations < max_iterations:
            iterations += 1
            # print(f"i={iterations}")
            n, b = root_node, deepcopy(board)

            # print(f"Root {len(n.children)}; Layer={n.layer}")
            # print(f"Board: {b}")

            # select leaf
            n = MCTS.selection(b, n)
            # print(f"Selection {len(n.children)}; Layer={n.layer}")
            # print(f"Board: {b}")

            # expand
            MCTS.expansion(b, n)
            # print(f"Expansion {len(n.children)}; Layer={n.layer}")
            # print(f"Board: {b}")
            
            # reselect after expansion
            n = MCTS.selection(b, n)
            
            # simulate
            end_state = MCTS.simulation(b, n)

            # check if end state is win
            is_win = BoardSupport.evaluate_is_win(end_state, player)

            # propagate
            MCTS.backpropagation(is_win, n)

        return Node.best_move(root_node)

    def select_best_move(self, board):
        """ Select the best move based on the results gathered during simulations """
        pass

if __name__ == "__main__":
    # Initialize MCTS with time and iteration limits
    mcts = MCTS(max_time=5, max_iterations=1000)

    # # test simulation
    # board = BoardSupport.create_board(11)
    # empty = BoardSupport.get_empty(board)
    # player = "R"
    # start_time = perf_counter()
    # MCTS.simulation(board, empty, player)
    # print(f"simulation time = {perf_counter() - start_time}") 
    # BoardSupport.check_winner(board)

    board_size = 5
    board = BoardSupport.create_board(board_size)
    player = "R"
    best_move = MCTS.make_move(board, player)
    print("Best move:", best_move)

