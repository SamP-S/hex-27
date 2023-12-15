import socket
from random import choice
from time import sleep, perf_counter
from copy import deepcopy
import numpy as np
from BoardSupport import BoardSupport
import sys


class Resistance():
    """ This class describes the electrical resistance heuristic calculation. """

    def __init__(self, board_size=11):
        """ pass in board size """

        self._board_size = board_size

    ### RESITSTANCE SYSTEMS

    def fill_connect(self, board, coord, player, checked):
        """ creates a set of all cells adjactent to coord of colour
            not including neighbours of colour """
        # tick that we have checked this cell
        checked[coord] = True
        connected = set()
        # iterate over neighbouring cells
        for coord in BoardSupport.get_neighbours(board, coord):
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
            for coord in BoardSupport.get_neighbours(board, cell):
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

    def resistance(self, board, player):
        """ Calculate the resistance heuristic of the board over empty nodes
        """
        
        # create index dictionaries to look up
        empty = BoardSupport.get_empty(board)
        index_to_location = empty
        num_empty = len(empty)
        location_to_index = {index_to_location[i]:i for i in range(len(index_to_location))}

        # current through internal nodes except that from source and dest
        # (zero except for source and dest connected nodes)
        I = np.zeros(num_empty)

        # conductance matrix
        # conductance = 1/R
        # V = I x R
        G = np.zeros((num_empty, num_empty))

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
        
        with open("./docs/kirchhoff.txt", "w") as f:
            f.write("source_connected:\n")
            # print(f"source_connected={source_connected}")
            for n in source_connected:
                j = location_to_index[n]
                I[j] += 1
                G[j,j] += 1
                f.write(str(n)+"\n")
                
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
                
            f.write("\ndest_connected:\n")
            # print(f"dest_connected={dest_connected}")
            for n in dest_connected:
                j = location_to_index[n]
                G[j,j] +=1
                f.write(str(n)+"\n")

            f.write("\nadjacency:\n")
            adjacency = self.get_connections(board, player, index_to_location, checked)
            # print(f"len={len(adjacency.keys())}; adjacency={adjacency.keys()}")
            for c1 in adjacency:
                j=location_to_index[c1]
                f.write(str(c1) + "\n")
                for c2 in adjacency[c1]:
                    i=location_to_index[c2]
                    G[i,j] -= 1
                    G[i,i] += 1
                    f.write("\t"+str(c2)+"\n")
            
            f.write("\nI:\n")
            for idx, i in enumerate(I):
                f.write(f"{idx}\t:\t{index_to_location[idx]}\t= {i}\n")
            
            f.write("\nG:\n")
            for j, row in enumerate(G):
                for i, elem in enumerate(row):
                    f.write(str(abs(int(elem))))
                f.write("\n")
            
            # calculate voltage matrix
            try:
                V_vec = np.linalg.solve(G,I)
            except Exception:
                return [], 0
            
            f.write("\nV:\n")
            for idx, v in enumerate(V_vec):
                f.write(f"{idx}\t:\t{index_to_location[idx]}\t= {v}\n")

        # current passing through each cell
        I_board = np.zeros((len(board), len(board)))

        # conductance from source to dest
        C = 0

        # iterate through voltage evtor to build current as board matrix
        # and conductance total from source to sink
        for i in range(num_empty):
            if index_to_location[i] in source_connected:
                I_board[index_to_location[i]] += abs(V_vec[i] - 1) / 2
            if index_to_location[i] in dest_connected:
                I_board[index_to_location[i]] += abs(V_vec[i]) / 2
            for j in range(num_empty):
                if(i!=j and G[i,j] != 0):
                    I_board[index_to_location[i]] += abs(G[i,j] * (V_vec[i] - V_vec[j])) / 2
                    if(index_to_location[i] in source_connected and
                    index_to_location[j] not in source_connected):
                        C += -G[i,j] * (V_vec[i] - V_vec[j])
        return I_board, C
    
    # pass evaluate function to AB to evaluate board positions then chose best move
    def evaluate_board(self, board, player):
        sim_board = deepcopy(board)

        # main matrices to calculate
        # I = current flowing through each connection of empty cell
        # C = total conductance from side to side attempting to join
        I1, C1 = self.resistance(sim_board, player)
        I2, C2 = self.resistance(sim_board, BoardSupport.opp_player(player))

        # returns ratio of conductivity
        # higher is better
        return C1 / C2


if (__name__ == "__main__"):
    # print("Resistance Testing")
    
    # def print_board(b):
    #     for j, row in enumerate(b):
    #         print(" "*j, end="")
    #         print(" ".join(row))

    board_size = 5
    player = "R"
    r = Resistance(board_size)
    board = BoardSupport.create_board(board_size)
    empty = BoardSupport.get_empty(board)

    eval = r.evaluate_board(deepcopy(board), player)
    print(eval)
    
    # print(f"Total conductivity={conductivity}")
    # print("Board")
    # print_board(board)
    # print("Currents")
    # print(I)

