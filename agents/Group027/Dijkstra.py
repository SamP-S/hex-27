from random import choice

class Dijkstra():
    """Dijkstra's algorithm for finding the shortest path across the board."""
    def make_path(self, board, colour):
        # opp_colour = "B" if colour == "R" else "R"
        prev, dist, path = self.pathfind(board, colour)
        return path
    
    def pathfind(self, board, colour):
        start = (-1, 0) if colour == "B" else (0, -1)
        end   = (11, 0) if colour == "B" else (0, 11) 

        dist = { start: 0 }
        prev = {}
        Q = { start }
        disc = { start }
                
        while len(Q) != 0:
            u = min(Q, key=lambda x: dist[x])
            Q.remove(u)

            neighbours = self.calculate_neighbours(u, board, colour)
            for v, w in neighbours.items():
                if v not in disc:
                    disc.add(v)
                    Q.add(v)
                    dist[v] = 1000000
                    prev[v] = None
                if v in Q:
                    alt = dist[u] + w
                    if alt < dist[v]:
                        dist[v] = alt
                        prev[v] = u
        
        path = []
        c = end
        while c != start:
            if c[0] >= 0 and c[0] < 11 and c[1] >= 0 and c[1] < 11 and board[c[1]][c[0]] != colour:
                path.append((c[1], c[0]))
            c = prev[c]
        
        return prev, dist, path
    
    # number of neighbours a tile has
    NEIGHBOUR_COUNT = 6

    # relative positions of neighbours, clockwise from top left
    I_DISPLACEMENTS = [-1, -1, 0, 1, 1, 0]
    J_DISPLACEMENTS = [0, 1, 1, 0, -1, -1]

    BRIDGE_NEIGHBOURS = [[0,1], [0,2], [1,3], [2,4], [3,5], [4,5]]
    I_BRIDGE_DISPLACEMENTS = [-2, -1, -1, 1, 1, 2]
    J_BRIDGE_DISPLACEMENTS = [1, -1, 2, -2, 1, -1]

    def calculate_neighbours(self, node, board, colour):
        opp_colour = ("R" if colour == "B" else "B")
        neighbours = {}
        if node[0] == -1:
            neighbours = {(0,x):(1 if board[x][0] == colour else 1) for x in range(0,11) if board[x][0] != opp_colour}
        elif node[1] == -1:
            neighbours = {(x,0):(1 if board[0][x] == colour else 1) for x in range(0,11) if board[0][x] != opp_colour}
        elif node[0] == 11:
            neighbours = {(10,x):(1 if board[x][10] == colour else 1) for x in range(0,11) if board[x][0] != opp_colour}
        elif node[1] == 11:
            neighbours = {(x,10):(1 if board[10][x] == colour else 1) for x in range(0,11) if board[0][x] != opp_colour}
        else:
            for idx in range(self.NEIGHBOUR_COUNT):
                n = (node[0] + self.I_DISPLACEMENTS[idx], node[1] + self.J_DISPLACEMENTS[idx])
                if (n[0] == -1):
                    if colour == "B":
                        neighbours[(-1, 0)] = 0
                elif (n[1] == -1):
                    if colour == "R":
                        neighbours[(0, -1)] = 0
                elif (n[0] == 11):
                    if colour == "B":
                        neighbours[(11, 0)] = 0
                elif (n[1] == 11):
                    if colour == "R":
                        neighbours[(0, 11)] = 0
                elif board[n[1]][n[0]] == colour:
                    neighbours[n] = 0
                elif board[n[1]][n[0]] != opp_colour:
                    neighbours[n] = 1

        return neighbours