import socket
from random import choice
from time import sleep, perf_counter
from copy import deepcopy
import numpy as np
from BoardSupport import Coordinates


class Resistance():
    """ This class describes the electrical resistance heuristic calculation. """

    def __init__(self, board_size=11):
        """ pass in board size """

        self._board_size = board_size
        
    def make_move(self, board, player):
        """Make a moev according to resistance conductivity
        """

        start_time = perf_counter()
        conductivity = self.score(deepcopy(board), player)
        move = np.unravel_index(conductivity.argmax(), conductivity.shape)
        print(f"R: move={move}; conductivity={conductivity.shape}; time={perf_counter() - start_time}")
        return move


    ### RESITSTANCE SYSTEMS

    def fill_connect(self, board, coord, player, checked):
        """ creates a set of all cells adjactent to coord of colour
            not including neighbours of colour """
        # tick that we have checked this cell
        checked[coord] = True
        connected = set()
        # iterate over neighbouring cells
        for coord in Coordinates.get_neighbours(board, coord):
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
            for coord in Coordinates.get_neighbours(board, cell):
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
        
        ### TECHNICALLY UNNECESSARY AS THE ENGINE WILL TELL US IF WIN
        # # win validation
        # win = self.check_winner(board)
        # if (win == 1):
        #     return np.zeros((len(board), len(board))), float("inf")
        # elif (win == -1):
        #     return np.zeros((len(board), len(board))), 0
        
        # create index dictionaries to look up
        index_to_location = empty
        num_empty = len(empty)
        location_to_index = {index_to_location[i]:i for i in range(len(index_to_location))}

        # current through internal nodes except that from source and dest
        # (zero except for source and dest connected nodes)
        I = np.zeros(num_empty)

        # conductance matrix such that G*V = I
        G = np.zeros((num_empty, num_empty))

        # print(f"shapes: I={I.shape}; G={G.shape}")

        checked = np.zeros((len(board), len(board)), dtype=bool)

        source_connected = set()
        if player == "R":
            for j in range(len(board)):
                coord = (0, j)
                if board[coord[0]][coord[1]] == "0":
                    source_connected.add(coord)
                elif board[coord[0]][coord[1]] == "B":
                    source_connected = source_connected | self.fill_connect(board, coord, player, checked)
        else:
            for i in range(len(board)):
                coord = (i, 0)
                if board[coord[0]][coord[1]] == "0":
                    source_connected.add(coord)
                elif board[coord[0]][coord[1]] == "R":
                    source_connected = source_connected | self.fill_connect(board, coord, player, checked)
        
        # print(f"source_connected={source_connected}")
        for n in source_connected:
            j = location_to_index[n]
            I[j] += 1
            G[j,j] += 1
            
        dest_connected = set()
        if player == "R":
            for j in range(len(board)):
                coord = ((len(board)-1, j))
                if board[coord[0]][coord[1]] == "0":
                    dest_connected.add(coord)
                elif board[coord[0]][coord[1]] == "B":
                    dest_connected = dest_connected | self.fill_connect(board, coord, player, checked)
        else:
            for i in range(len(board)):
                coord = (i, len(board)-1)
                if board[coord[0]][coord[1]] == "0":
                    dest_connected.add(coord)
                elif board[coord[0]][coord[1]] == "R":
                    dest_connected = dest_connected | self.fill_connect(board, coord, player, checked)
            
        
        # print(f"dest_connected={dest_connected}")
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

        V_board = np.zeros((len(board), len(board)))
        for i in range(num_empty):
            V_board[index_to_location[i]] = V[i]

        #current passing through each cell
        Il = np.zeros((len(board), len(board)))
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

        # print(Il)
        return Il, C

    def score(self, board, player):
        # Q is dictionary
        Q = {}
        empty = Coordinates.get_empty(board)
        #filled_fraction = (boardsize**2-num_empty+1)/boardsize**2

        # main matrices to calculate
        # I = current flowing through each connection of empty cell
        # C = total conductance from side to side attempting to join
        I1, C1 = self.resistance(board, empty, player)
        I2, C2 = self.resistance(board, empty, self.opp_player(player))

        # print(f"C1={C1}; C2={C2}")

        # layers of colour with paddding
        # print(f"I1={I1.shape}; C1={C1}")
        # print(f"I2={I2.shape}; C2={C2}")

        empty = Coordinates.get_empty(board)
        for i, coord in enumerate(empty):

            # # THIS IS AN APPROXIMATION OF THE CURRENT OF THE
            # # NEW BOARD IF CELL IS TAKEN AS THE MOVE
            # #this makes some sense as an approximation of
            # #the conductance of the next state
            # C1_prime = C1 + I1[cell]**2/(3*(1-I1[cell]))
            # C2_prime = max(0,C2 - I2[cell])
            sim_board = deepcopy(board)
            sim_board[coord[0]][coord[1]] = player
            sim_empty = deepcopy(empty)
            sim_empty.pop(i)

            I1_prime, C1_prime = self.resistance(sim_board, sim_empty, player)
            I2_prime, C2_prime = self.resistance(sim_board, sim_empty, self.opp_player(player))

            # print(f"C1_prime={C1_prime}; C2_prime={C2_prime}")

            # fill Q dictionary with estimate conductivity values
            # for board if cell take as move
            if(C1_prime>C2_prime):
                Q[coord] = min(1,max(-1,1 - C2_prime/C1_prime))
            else:
                Q[coord] = min(1,max(-1,C1_prime/C2_prime - 1))

        # create matrix of -1s of board size
        output = -1 * np.ones((len(board), len(board)))

        # iterate through Q dictionary
        # fill output matrix with board conductivity if that cell is selected
        # HIGHER is better
        for coord, value in Q.items():
            output[coord[0]][coord[1]] = value
        # return new matrix of values
        return output

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
    print("Resistance.py has no main")
