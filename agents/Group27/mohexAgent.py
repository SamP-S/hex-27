import socket
from random import choice
from time import sleep
import subprocess
import time
import sys
import select
sys.stdout = open('output', 'w')
MOVES =[]
# Blue & White connect horizontally
# Red & Black vertically
mohex_colour_map = {'R': 'Bl', 'Bl': 'R', 'B': 'W', 'W': 'B'}
# Colour mapping



class mohexAgent():
    """This class describes an agent that interfaces with the MoHex
    executable. It is a finite-state machine that cycles through
    waiting for input and sending moves.
    """

    HOST = "127.0.0.1"
    PORT = 1234

    def __init__(self):
        # Start the subprocess when the agent is initialized
        self._start_subprocess()

    def _start_subprocess(self):
        # Replace 'your_c_agent_executable' with the actual path to your C agent executable
        self._process = subprocess.Popen(["./agents/Group27/mohex"], stdin=subprocess.PIPE, stdout=subprocess.PIPE,  
                                         stderr=subprocess.DEVNULL, 
                                         text=True)
        time.sleep(1)
        self._send_mohex_command("boardsize 11 11")
        response = self._read_mohex_response()
        print("Game start")

    def _terminate_subprocess(self):
        # Terminate the subprocess when the agent is closed
        self._process.terminate()
        #print("Victory!")

    def run(self):
        """A finite-state machine that cycles through waiting for input
        and sending moves.
        """
        
        self._board_size = 0
        self._board = []
        self._colour = ""
        self._turn_count = 1
        self._choices = []
        self._opponent_moves = []
        self._opp_swapped = False
        
        states = {
            1: mohexAgent._connect,
            2: mohexAgent._wait_start,
            3: mohexAgent._make_move,
            4: mohexAgent._wait_message,
            5: mohexAgent._close
        }

        res = states[1](self)
        while (res != 0):
            res = states[res](self)
    
    

    def _connect(self):
        """Connects to the socket and jumps to waiting for the start
        message.
        """
        
        self._s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._s.connect((mohexAgent.HOST, mohexAgent.PORT))

        return 2

    def _wait_start(self):
        """Initialises itself when receiving the start message, then
        answers if it is Red or waits if it is Blue.
        """
        
        data = self._s.recv(1024).decode("utf-8").strip().split(";")
        if (data[0] == "START"):
            self._board_size = int(data[1])
            for i in range(self._board_size):
                for j in range(self._board_size):
                    self._choices.append((i, j))
            self._colour = data[2]

            if (self._colour == "R"):
                return 3
            else:
                return 4

        else:
            # print("ERROR: No START message received.")
            return 0

    def _make_move(self):
        """Updates mohex board and requests it to generate move
        Then plays move
        """
        # print(f"Colour: {self._colour}")
        if (self._turn_count == 1):
            # play first move
            mohex_colour = mohex_colour_map[self._colour][0]
            self._send_mohex_command(f"play {mohex_colour} g7")
            response = self._read_mohex_response()
            move = f"{6},{6}\n"
            self._s.sendall(bytes(move, "utf-8"))
            MOVES.append([self._colour, move])
            print("DEBUG: Bot move: ", move)
        elif (self._turn_count == 2 and choice([0, 1]) == 1):
            msg = "SWAP\n"
            self._s.sendall(bytes(msg, "utf-8"))
        else:
            self.play_round()

        return 4
    
    def _wait_message(self):
        """Waits for a new change message when it is not its turn."""
        self._turn_count += 1

        data = self._s.recv(1024).decode("utf-8").strip().split(";")

        if (data[0] == "END" or data[-1] == "END"):
            return 5
        else:
            if (data[1] == "SWAP"):
                self._colour = self.opp_colour()
                self._opp_swapped = True # Check if opponent used swap move
                print("DEBUG: Opponent swapped")
            else:
                x, y = data[1].split(",")
                move = (int(x), int(y))
                self._choices.remove(move)
                self._opponent_moves.append(move)  # Store opponent's move

            if (data[-1] == self._colour):
                return 3

        return 4

    def _close(self):
        # Close the socket
        self._s.close()
        
        # Terminate the subprocess
        self._terminate_subprocess()
        print(MOVES)

        return 0

    def opp_colour(self):
        """Returns the char representation of the colour opposite to the
        current one.
        """
        
        if self._colour == "R":
            return "B"
        elif self._colour == "B":
            return "R"
        else:
            return "None"
    
    def _send_mohex_command(self, command):
        if self._process.poll() is None:  # Check if the process is still running
            self._process.stdin.write(command + '\n')
            self._process.stdin.flush()
        else:
            raise Exception("Cannot send command: The process has terminated")
        print(f"Command sent: {command}")

    # def _read_mohex_response(self):
    #     response = ''
    #     while not response:
    #         output = self._process.stdout.readline().strip()
    #         if output == '' or output.endswith('\n'):
    #             continue  # Skip empty or incomplete lines
    #         response = output 
    #     # print(f"RESPONSE: {response}")
    #     return response
    def _read_mohex_response(self, timeout=15.0):
        response = 'timeout'
        end_time = time.time() + timeout
        while time.time() < end_time:
            ready, _, _ = select.select([self._process.stdout], [], [], end_time - time.time())
            if ready:
                output = self._process.stdout.readline().strip()
                if output == '' or output.endswith('\n'):
                    continue  # Skip empty or incomplete lines
                response = output
                break
        print(f"RESPONSE: {response}")
        return response
    
    def mohex_to_hex_board(self, val1, val2):
        firstval = int(val2)-1
        secondval = ord(val1)-ord('a')
        return firstval, secondval
    
    def hex_to_mohex_board(self, val1, val2):
        firstval = chr(ord('a') + int(val2))
        secondval = val1+1
        return firstval, secondval
    
    def separate_letter_and_number(self, input_str):
        letter = ''.join(char for char in input_str if char.isalpha())
        number = ''.join(char for char in input_str if char.isdigit())
        return letter, number
    
    def play_round(self):
        """Play a round of Hex."""
        # First we need to play opponents last move on MoHex
        # Check if opponent swapped or not
        if self._opp_swapped:
            self._opp_swapped = False
        else:
            # Play opponents last move
            opp_move = self._opponent_moves[-1]
            MOVES.append([self.opp_colour(), opp_move])
            opp_move = self.hex_to_mohex_board(opp_move[0], str(opp_move[1]))
            opp_mohex_colour = mohex_colour_map[self.opp_colour()][0]
            self._send_mohex_command(f"play {opp_mohex_colour} {opp_move[0]+str(opp_move[1])}")
            response = self._read_mohex_response()
            print(f"DEBUG: Opponent move: {self._opponent_moves[-1]}")
        
        # Then we need to generate our move
        mohex_colour = mohex_colour_map[self._colour][0]
        self._send_mohex_command(f"genmove {mohex_colour}")
        response = self._read_mohex_response()
        print("Response: ", response)
        if response == 'timeout':
            print("Timeout")
            sys.exit()
        
        # Send move to server
        print(f"RESPONSE: {response}")
        move = self.separate_letter_and_number(response)
        move = self.mohex_to_hex_board(move[0], move[1])
        msg = f"{move[0]},{move[1]}\n"
        # Then we need to play our move
        MOVES.append([self._colour, msg])
        print("DEBUG: Bot move: ", msg)
        self._s.sendall(bytes(msg, "utf-8"))

if (__name__ == "__main__"):
    agent = mohexAgent()
    agent.run()

