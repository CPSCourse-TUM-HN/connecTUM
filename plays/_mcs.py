import modules.board_param as param
from game_board import Board
from copy import deepcopy

import numpy as np
import random
from typing import List
from dataclasses import dataclass, field
from itertools import cycle

def mcs_play(board: Board, n_iterations):
    """
    Bot that plays Connect 4 using simple Monte Carlo Simulation

    @param board:
        Board object representing current board state

    @param n_iterations:
        number of simulations run
    """
    # If there's only one move possible, return that
    if len(board.get_valid_locations()) == 1:
        return board.get_valid_locations()[0]


    @dataclass  
    class Node():
        board: Board
        col: int
        wins: int = field(default=0, init=False)
        n_visits: int = field(default=0, init=False)
    
    child_nodes: List[Node] = []
    for col in board.get_valid_locations():
        new_board = deepcopy(board)
        new_board.drop_piece(col, param.BOT_PIECE)
        # If immediate win
        if new_board.winning_move(param.BOT_PIECE):
            return col
        node = Node(new_board, col)
        child_nodes.append(node)


    for _ in range(n_iterations):
        chosen_node = random.choice(child_nodes)

        # Simulate / Rollout
        pieces = cycle([param.PLAYER_PIECE, param.BOT_PIECE])
        sim_board = deepcopy(chosen_node.board)
        for piece in pieces:
            col = random.choice(sim_board.get_valid_locations())
            sim_board.drop_piece(col, piece)
            if sim_board.winning_move(piece):
                if piece == param.BOT_PIECE:
                    result = 1
                else:
                    result = -10
                break
            if not sim_board.get_valid_locations(): # Draw
                result = 0
                break
        
        chosen_node.n_visits += 1
        chosen_node.wins += result

    return max(child_nodes, key=lambda node : (node.wins / node.n_visits)).col
