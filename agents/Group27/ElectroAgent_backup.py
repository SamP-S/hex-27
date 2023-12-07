import socket
from random import choice
from time import sleep, perf_counter
from copy import deepcopy
import numpy as np


class ElectroAgent():
    """This class describes the default Hex agent. It will randomly send a
    valid move at each turn, and it will choose to swap with a 50% chance.
    """

    HOST = "127.0.0.1"
    PORT = 1234

    DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1), (-1, 1), (1, -1)]

    def __init__(self, eval_func=1):
        if eval_func == 0:
            self.evaluate_board = self.flat_board_evaluation
        elif eval_func == 1:
            self.evaluate_board = self.simple_board_evaluation
        else:
            print("ERROR: NO EVAL FUNCTION")

    def run(self):
        """A finite-state machine that cycles through waiting for input
        and sending moves.
        """
        
        self._board_size = 0
        self._board = []
        self._colour = ""
        self._turn_count = 1
        self._choices = []
        self._red_moves = []
        self._blue_moves = []
        self.node_count = 0
        
        states = {
            1: ElectroAgent._connect,
            2: ElectroAgent._wait_start,
            3: ElectroAgent._make_move,
            4: ElectroAgent._wait_message,
            5: ElectroAgent._close
        }

        res = states[1](self)
        while (res != 0):
            res = states[res](self)

    def _connect(self):
        """Connects to the socket and jumps to waiting for the start
        message.
        """

        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._s.connect((ElectroAgent.HOST, ElectroAgent.PORT))
        return 2

    def _wait_start(self):
        """Initialises itself when receiving the start message, then
        answers if it is Red or waits if it is Blue.
        """
        
        data = self._s.recv(1024).decode("utf-8").strip().split(";")
        if (data[0] == "START"):
            self._board = []
            self._board_size = int(data[1])
            
            for i in range(self._board_size):
                row = []
                for j in range(self._board_size):
                    self._choices.append((i, j))
                    row.append("0")
                self._board.append(row)
            self._colour = data[2]

            print(f"boardsize: {self._board_size}")
            print(f"colour: {self._colour}")

            if (self._colour == "R"):
                return 3
            else:
                return 4

        else:
            print("ERROR: No START message received.")
            return 0

    def _make_move(self):
        """Makes a random valid move. It will choose to swap with
        a coinflip.
        """
        # print(f"board: {self._board}")
        # print(f"choices: {self._choices}")
        print(f"turncount: {self._turn_count}")
        
        if (self._turn_count == 2 and choice([0, 1]) == 1):
            msg = "SWAP\n"
        else:
            # move = choice(self._choices)
            self.node_count = 0
            start_time = perf_counter()

            # resistance checking
            print("resistance")
            # num_empty, empty = self.get_empty(self._board)
            # I1, C1 = self.resistance(deepcopy(self._board), empty, self._colour)
            # I2, C2 = self.resistance(deepcopy(self._board), empty, self.opp_player(self._colour))

            # print(f"I1={I1.shape}; C1={C1.shape}")
            # print(f"I2={I2.shape}; C2={C2.shape}")

            res = self.score(deepcopy(self._board), self._colour)
            print(f"res.shape={res.shape}; res={res}")

            # ab
            val, move = self.alpha_beta(deepcopy(self._board), deepcopy(self._choices), self._colour, 3)
            print(f"ab finish: val={val}; move={move}; nodes={self.node_count}; time={perf_counter() - start_time}")
            # self._choices.remove(move)
            # self._board[int(move[0])][int(move[1])] = self._colour
            # if self._colour == "R":
            #     self._red_moves.append(move)
            # elif self._colour == "B":
            #     self._blue_moves.append(move)
            msg = f"{move[0]},{move[1]}\n"
        
        self._s.sendall(bytes(msg, "utf-8"))

        return 4

    ### RESITSTANCE SYSTEMS

    def get_neighbours(self, coord):
        """ Return list of coordinates of neighbouring cells
            Filters coordinates outside of boardspace
        """
        neighbours = []
        for dx, dy in self.DIRECTIONS:
            x = coord[0] + dx
            y = coord[1] + dy
            if x >= 0 and x < self._board_size and y >= 0 and y < self._board_size:
                neighbours.append((x, y))
        return neighbours
            

    def get_empty(self, board):
        """ Creates list of coordinates of all unclaimed cells """
        count = 0
        coords = []
        for i in range(self._board_size):
            for j in range(self._board_size):
                if (board[i][j]) == "0":
                    count += 1
                    coords.append((i, j))
        return count, coords

    def fill_connect(self, board, coord, player, checked):
        """ creates a set of all cells adjactent to coord of colour
            not including neighbours of colour """
        # tick that we have checked this cell
        checked[coord] = True
        connected = set()
        # iterate over neighbouring cells
        for coord in self.get_neighbours(coord):
            if(not checked[coord]):
                # if neighbour is same colour and then combine that neighbours connected set
                if(board[coord[0]][coord[1]] == player):
                    connected = connected | self.fill_connect(board, coord, player, checked)
                # if neightbour is not other colour then add to connected set
                elif(board[coord[0]][coord[1]] == "0"):
                    connected.add(coord)
        return connected

    def get_connections(self, board, player, empty, checked):
        """ get dictionary of adjactent cells that are empty """
        # create empty dictionary of cell -> set
        connections = {cell:set() for cell in empty}
        # iterate over all empty cells
        for cell in empty:
            # neighbors of cell
            for coord in self.get_neighbours(cell):
                # if not already checked
                if(not checked[coord]):
                    # check if cell is colour
                    if(board[coord[0]][coord[1]] == player):
                        # if neighbour is owned by player
                        # find connection set of neighbour
                        # and combine the connections to themselves??
                        connected_set = self.fill_connect(board, coord, player, checked)
                        for c1 in connected_set:
                            for c2 in connected_set:
                                connections[c1].add(c2)
                                connections[c2].add(c1)
                    elif(board[coord[0]][coord[1]] == "0"):
                        connections[cell].add(coord)
        return connections

    def resistance(self, board, empty, player):
        """ Calculate the resistance heuristic of the board over empty nodes
        """

        # win validation
        win = self.check_winner(board)
        if (win == 1):
            return np.zeros((self._board_size, self._board_size)), float("inf")
        elif (win == -1):
            return np.zeros((self._board_size, self._board_size)), 0
        
        # create index dictionaries to look up
        index_to_location = empty
        num_empty = len(empty)
        location_to_index = {index_to_location[i]:i for i in range(len(index_to_location))}

        # current through internal nodes except that from source and dest
        # (zero except for source and dest connected nodes)
        I = np.zeros(num_empty)

        # conductance matrix such that G*V = I
        G = np.zeros((num_empty, num_empty))

        print(f"shapes: I={I.shape}; G={G.shape}")

        checked = np.zeros((self._board_size, self._board_size), dtype=bool)

        
        source_connected = set()
        if player == "R":
            for i in range(self._board_size):
                if board[i][0] == "0":
                    source_connected.add((i, 0))
                elif board[i][0] == "R":
                    source_connected = source_connected | self.fill_connect(board, (i,0), player, checked)
        else:
            for j in range(self._board_size):
                if board[0][j] == "0":
                    source_connected.add((0, j))
                elif board[0][j] == "B":
                    source_connected = source_connected | self.fill_connect(board, (0, j), player, checked)
        
        print(f"source_connected={source_connected}")
        for n in source_connected:
            j = location_to_index[n]
            I[j] += 1
            G[j,j] += 1
            
        dest_connected = set()
        if player == "R":
            for i in range(self._board_size):
                if board[i][0] == "0":
                    dest_connected.add((i, self._board_size-1))
                elif board[i][0] == "R":
                    dest_connected = dest_connected | self.fill_connect(board, (i,self._board_size-1), player, checked)
        else:
            for j in range(self._board_size):
                if board[0][j] == "0":
                    dest_connected.add((self._board_size-1, j))
                elif board[0][j] == "B":
                    dest_connected = dest_connected | self.fill_connect(board, (self._board_size-1, j), player, checked)
        
        print(f"dest_connected={dest_connected}")
        for n in dest_connected:
            j = location_to_index[n]
            G[j,j] +=1

        adjacency = self.get_connections(board, player, index_to_location, checked)
        # print(f"len={len(adjacency.keys())}; adjacency={adjacency.keys()}")
        for c1 in adjacency:
            j=location_to_index[c1]
            for c2 in adjacency[c1]:
                i=location_to_index[c2]
                G[i,j] -= 1
                G[i,i] += 1

        # print(I)
        # print(G)
        #voltage at each cell
        try:
            V = np.linalg.solve(G,I)
        #slightly hacky fix for rare case of isolated empty cells
        #happens rarely and fix should be fine but could improve
        except np.linalg.linalg.LinAlgError:
            V = np.linalg.lstsq(G,I)[0]

        V_board = np.zeros((self._board_size, self._board_size))
        for i in range(num_empty):
            V_board[index_to_location[i]] = V[i]

        #current passing through each cell
        Il = np.zeros((self._board_size, self._board_size))
        #conductance from source to dest
        C = 0

        for i in range(num_empty):
            if index_to_location[i] in source_connected:
                Il[index_to_location[i]] += abs(V[i] - 1)/2
            if index_to_location[i] in dest_connected:
                Il[index_to_location[i]] += abs(V[i])/2
            for j in range(num_empty):
                if(i!=j and G[i,j] != 0):
                    Il[index_to_location[i]] += abs(G[i,j]*(V[i] - V[j]))/2
                    if(index_to_location[i] in source_connected and
                    index_to_location[j] not in source_connected):
                        C+=-G[i,j]*(V[i] - V[j])
        return Il, C

    def score(self, board, player):
        # Q is dictionary
        Q = {}
        num_empty, empty = self.get_empty(board)
        #filled_fraction = (boardsize**2-num_empty+1)/boardsize**2

        # main matrices to calculate
        # I = current flowing through each connection of empty cell
        # C = total conductance from side to side attempting to join
        I1, C1 = self.resistance(board, empty, player)
        I2, C2 = self.resistance(board, empty, self.opp_player(player))

        # layers of colour with paddding
        print(f"I1={I1.shape}; C1={C1.shape}")
        print(f"I2={I2.shape}; C2={C2.shape}")

        num_empty, empty = self.get_empty(board)
        for cell in empty:

            # THIS IS AN APPROXIMATION OF THE CURRENT OF THE
            # NEW BOARD IF CELL IS TAKEN AS THE MOVE
            #this makes some sense as an approximation of
            #the conductance of the next state
            C1_prime = C1 + I1[cell]**2/(3*(1-I1[cell]))
            C2_prime = max(0,C2 - I2[cell])

            # fill Q dictionary with estimate conductivity values
            # for board if cell take as move
            if(C1_prime>C2_prime):
                Q[cell] = min(1,max(-1,1 - C2_prime/C1_prime))
            else:
                Q[cell] = min(1,max(-1,C1_prime/C2_prime - 1))

        # create matrix of -1s of board size
        output = -1 * np.ones((self._board_size, self._board_size))
        # iterate through Q dictionary
        # fill output matrix with board conductivity if that cell is selected
        # HIGHER is better
        for cell, value in Q.items():
            output[cell[0]][cell[1]] = value
        # return new matrix of values
        return output 




    def dfs(self, board, player, coord, front, back):
        """ Depth First Search for win checking 
            Red top->bottom
            Blue left->right """
        # print(f"dfs: i={i}; j={j}; board={board}")
        i = coord[0]
        j = coord[1]

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
        for coord in self.get_neighbours((i,j)):
            # check neighbours
            next_front, next_back = self.dfs(board, player, coord, front, back)
            if next_front and next_back:
                return True, True

        # no neighbours or connections to edges
        return front, back

    def check_winner(self, board):
        """ Checks if there is a connection from one side of the board to the other
            Red top->bottom
            Blue left->right
            Return 1 for Red win, -1 for Blue win, 0 for no winner """

        # start_time = perf_counter()
        # iterate over top row to start dfs search
        for i in range(self._board_size):
            front, back = self.dfs(deepcopy(board), "R", (i, 0), False, False)
            if board[i][0] == 'R' and front and back:
                # print(f"AB WIN RED ({i},{0})")
                # print(f"check_win time: {perf_counter() - start_time}")
                return 1
        #  iterate over left column to start dfs search
        for j in range(self._board_size):
            front, back = self.dfs(deepcopy(board), "B", (0, j), False, False)
            if board[0][j] == 'B' and front and back:
                # print(f"AB WIN BLUE ({0},{j})")
                # print(f"check_win time: {perf_counter() - start_time}")
                return -1
        # print(f"check_win time: {perf_counter() - start_time}")
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
        
    def simple_board_evaluation(self, board, player):
        """ return value of current board according to player as float """
        return 0.5

    def _wait_message(self):
        """Waits for a new change message when it is not its turn."""

        self._turn_count += 1

        data = self._s.recv(1024).decode("utf-8").strip().split(";")
        if (data[0] == "END" or data[-1] == "END"):
            return 5
        else:

            if (data[1] == "SWAP"):
                self._colour = self.opp_player(self._colour)
            else:
                x, y = data[1].split(",")
                print("data:", data)
                self._choices.remove((int(x), int(y)))
                self._board[int(x)][int(y)] = data[-1]
                if data[-1] == "R":
                    self._red_moves.append((int(x), int(y)))
                elif data[-1] == "B":
                    self._blue_moves.append((int(x), int(y)))
                print(self._board)
            if (data[-1] == self._colour):
                return 3

        return 4

    def _close(self):
        """Closes the socket."""

        self._s.close()
        return 0

    def opp_player(self, player):
        """Returns the char representation of the colour opposite to the
        current one.
        """
        
        if player == "R":
            return "B"
        elif player == "B":
            return "R"
        else:
            return "None"


if (__name__ == "__main__"):
    agent = ElectroAgent()
    agent.run()
