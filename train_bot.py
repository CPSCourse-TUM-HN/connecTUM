from main import *
import itertools
from time import time
from connect4 import Position, Solver
import multiprocessing as mp

SENTINEL = None

# board_states = []

# bot_start_states = []
# player_start_states = []

def ret_game_states():
    for start_piece in (BOT_PIECE, PLAYER_PIECE):
        piece = itertools.cycle([BOT_PIECE, PLAYER_PIECE])
        if start_piece is PLAYER_PIECE: next(piece)
        n_turns_rng = range(0, 41, 2) if start_piece is BOT_PIECE else range(1,42,2)

        for n_turns in n_turns_rng:
            move_seqs = (seq for seq in itertools.product(range(COLUMN_COUNT), repeat=n_turns))
            for move_seq in move_seqs:
                board = create_board()
                for col in move_seq:
                    if not is_valid_location(board, col):
                        break
                    game_over = play_turn(board, col, next(piece), display_board=False)
                    if game_over:
                        break
            else: # no break - valid playable game state
                yield board

        for n_turns in n_turns_rng:
            board = create_board()
            unfilled_cols = list(range(COLUMN_COUNT))
            for i in range(n_turns):
                for col in unfilled_cols:
                    if not is_valid_location(board, col):
                        unfilled_cols.remove(col)
                        continue

def combinations_with_max_repeats(iterable, r, max_repeats):
    """
    Optimized version that pre-calculates which combinations are possible.

    Parameters
    ----------

    iterable:
        list of options
    r:
        combination of length r is returned
    max_repeats:
        maximum number of times an option can be repeated
    """
    items = list(set(iterable))  # Remove duplicates
    n = len(items)
    
    def generate_combinations(pos, current, remaining, counts):
        if remaining == 0:
            yield tuple(current)
            return
        
        if pos >= n:
            return
        
        item = items[pos]
        
        # Try adding 0 to min(max_repeats, remaining) copies of current item
        for copies in range(min(max_repeats + 1, remaining + 1)):
            new_current = current + [item] * copies
            new_remaining = remaining - copies
            
            yield from generate_combinations(pos + 1, new_current, new_remaining, counts)
    
    yield from generate_combinations(0, [], r, {})


def get_game_states():
    """Generator of valid board game states"""

    cols = [i for i in range(COLUMN_COUNT)]
    # for n_turns in range(ROW_COUNT * COLUMN_COUNT):
    for n_turns in range(2):
        print("\x1b[1;31m" + str(n_turns) + "\033[0m")
        for combo in combinations_with_max_repeats(cols, n_turns, ROW_COUNT):
            n_bot_moves = n_turns // 2
            all_combinations = itertools.combinations(range(len(combo)), n_bot_moves)
            for bot_indices in all_combinations:
                board = create_board()
                for turn, col in enumerate(combo):
                    piece = BOT_PIECE if (turn in bot_indices) else PLAYER_PIECE
                    play_turn(board, col, piece, display_board=False)
                yield board
        

def get_optimal_move(board):
    position = Position(board)
    solver = Solver()
    scores = solver.analyze(position, False)
    return scores

# Multiprocessing functions

def produce_states(state_queue, num_workers):
    print(f"Producer: {mp.current_process().name}")
    for game_state in get_game_states():
        state_queue.put(game_state)
    # Send stop signal to solvers
    for _ in range(num_workers):
        state_queue.put(SENTINEL) # Sentinel for solvers

def solver(state_queue, result_queue):
    while True:
        game_state = state_queue.get()
        if game_state is SENTINEL:
            break
        optimal_move = get_optimal_move(game_state)
        # optimal_move = 3
        print(f"{mp.current_process().name} -> {optimal_move}")
        result_queue.put((board2key(game_state), optimal_move))
    result_queue.put(SENTINEL)  # Sentinel for collector

def collector(result_queue, num_workers, output_file):
    results = {}
    done_signals = 0
    while done_signals < num_workers:
        item = result_queue.get()
        # print(f"collector ({mp.current_process().name}): {item}")
        if item is SENTINEL:
            done_signals += 1
        else:
            game_state, move = item
            results[game_state] = move
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)


if (__name__ == "__main__"):
    mp.freeze_support()

    lookup_table_loc = "big_lookup_table.json"
    
    # manager = mp.Manager()
    task_queue = mp.Queue()
    result_queue = mp.Queue()

    num_workers = mp.cpu_count()
    # num_workers = 2
    print(f"num_workers = {num_workers}")
    print(mp.current_process().name)

    start_time = time()

    producer_process = mp.Process(target=produce_states, args=(task_queue, num_workers))
    producer_process.start()

    workers = []
    for _ in range(num_workers):
        p = mp.Process(target=solver, args=(task_queue, result_queue))
        p.start()
        workers.append(p)

    collector_process = mp.Process(target=collector, args=(result_queue, num_workers, lookup_table_loc))
    collector_process.start()

    producer_process.join()
    for p in workers:
        p.join()
    collector_process.join()

    end_time = time()
    elapsed = end_time - start_time
    minutes, seconds = divmod(elapsed, 60)
    print(f"Time taken: {int(minutes)} minutes and {seconds:.2f} seconds")