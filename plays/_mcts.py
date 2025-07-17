import random
import math
from typing import List
from itertools import cycle
from copy import deepcopy

import modules.board_param as param
from game_board import Board

class MCTSNode:
    """
    Parameters
    ----------

    board : Board
        current board state

    parent : MCTSNode
        parent node

    piece : [param.BOT_PIECE | param.PLAYER_PIECE]
        current piece to play

    opponent_piece : [param.BOT_PIECE | param.PLAYER_PIECE]
        piece of opponent

    last_move : int
        column played by opponen to get to this node

    total_visits : int
        number of times this node was visited

    total_wins : int
        Number of wins by opponent (parent node) when played through this node

    children : List[MCTSNode]
        Child nodes
    """
    def __init__(self, board: Board, piece, parent = None, last_move: int | None = None):
        self.board = board
        self.piece = piece # BOT_PIECE or PLAYER_PIECE
        self.opponent_piece = param.BOT_PIECE if piece == param.PLAYER_PIECE else param.PLAYER_PIECE
        self.parent: MCTSNode = parent
        self.last_move = last_move
        self.total_visits: int = 0
        self.total_parent_wins: int = 0
        self.children: List[MCTSNode] = []


class MCTS_Tree:
    """
    Parameters
    ----------
    root_node : MCTSNode
        Starting node. Current board state

    c : float
        Exploration constant. Higher values favor more exploration
    """
    def __init__(self, root_node: MCTSNode, c: float = math.sqrt(2), lookup_table: dict = dict()):
        self.root_node = root_node
        self.c = c
        self.total_parent_visits: int = 0

        self.lookup_table = lookup_table

    def get_ucb(self, node: MCTSNode):
        """
        Compute the Upper Confidence Bound (UCB) of this node

        The UCB formula balances exploration and exploitation in tree search algorithms.
        It is given by:

            UCB = (w_i / n_i) + c * sqrt(ln(N) / n_i)


        Where:
            w_i : int
                node.total_wins
            n_i : int
                node.total_visits
            N   : int
                Total number of global visits
            c   : self.c
                Exploration constant. Higher values encourage more exploration.

        Returns:
            float:
                The UCB score for the child node.
        """
        if not (node.total_visits):
            return math.inf
        else:
            value_estimate = node.total_parent_wins / (node.total_visits)
            exploration = math.sqrt(math.log(node.parent.total_visits) / (node.total_visits))
            ucb_score =  value_estimate + self.c * exploration
            return ucb_score
        
    def select(self):
        """
        Iteratively go down the explored search tree selecting the child node with the highest UCB
        until a terminal node is reached.
        """
        current_node = self.root_node

        while current_node.children:
            current_node = max(current_node.children, key=lambda node : self.get_ucb(node))
        
        return current_node
    

    def expand_and_get_child(self, node: MCTSNode):
        """
        Expand search tree by adding new children to `node` for each possible next move
        """
        board = node.board

        # If already won, don't expand, return the parent
        if board.winning_move(param.BOT_PIECE) or board.winning_move(param.PLAYER_PIECE):
            return node
        
        playable_cols = board.get_valid_locations()
        playable_cols = sorted(playable_cols, key= lambda x : abs(x - 3)) # Explore center moves first

        # If draw, don't expand, return the parent
        if not playable_cols:
            return node

        children = []
        for col in playable_cols:
            new_board = deepcopy(board)
            new_board.play_turn(col, node.piece, display_board=False)

            child = MCTSNode(new_board, node.opponent_piece, node, col)
            children.append(child)
        
            # If this move wins the game
            if new_board.winning_move(node.piece):
                node.children.append(child)
                return child
        
        node.children = children # Only expands if next move doesn't immediately win
        return random.choice(node.children)
    

    def simulate(self, node: MCTSNode):
        """
        Game is simulated from node with random play

        :param node :
            Starting node from which game is simulated

        :return winner :
            winning piece, or param.EMPTY in case of a draw
        """

        if node.board.winning_move(node.opponent_piece):
            return node.opponent_piece

            
        pieces = cycle([node.piece, node.opponent_piece])
        sim_board = deepcopy(node.board)
        for piece in pieces:
            if not sim_board.get_valid_locations(): # Draw
                return param.EMPTY
            
            col = random.choice(sim_board.get_valid_locations())
            sim_board.drop_piece(col, piece)
            if sim_board.winning_move(piece):
                return piece
            
    def backpropagate(self, node: MCTSNode, winner: int):
        while node:
            node.total_visits += 1
            if winner == node.opponent_piece:
                node.total_parent_wins += 1
            elif winner == node.piece:
                node.total_parent_wins -= 1

            node = node.parent

def mcts_play(board, n_iterations, c):

    root = MCTSNode(board, param.BOT_PIECE)
    tree = MCTS_Tree(root, c)
    for _ in range(n_iterations):
        node = tree.select()
        child_node = tree.expand_and_get_child(node)
        winner = tree.simulate(child_node)
        tree.backpropagate(child_node, winner)

    # Select optimal move: get move of child with highest number of visits (Robust Child)
    return max(root.children, key= lambda node : node.total_visits).last_move