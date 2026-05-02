#python chess is the library used to simulate legal moves and import fen notation
import chess
#graphical game library
import pygame

import random
import sys
import os
import time
from collections import OrderedDict

# Get the correct path whether running as script or frozen exe
if getattr(sys, 'frozen', False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))

def asset_path(relative_path):
    return os.path.join(application_path, relative_path)

scale_factor = 0.75

#debugging
debug = False
debug_fen = "3B4/5Q1k/8/3p2Pp/8/3p1P2/1PB2P2/4RRK1 b - - 3 51"
debug_playerColour = chess.BLACK

pygame.init()
pygame.font.init()

tile_Size = 100 * scale_factor
board_Size = tile_Size * 8
boardOffset = 10 * scale_factor

piecepositionDict = {
    "k": (0, 0), "q": (tile_Size, 0), "r": (2*tile_Size, 0),
    "b": (3*tile_Size, 0), "n": (4*tile_Size, 0), "p": (5*tile_Size, 0),
    "K": (0, tile_Size), "Q": (tile_Size, tile_Size), "R": (2*tile_Size, tile_Size),
    "B": (3*tile_Size, tile_Size), "N": (4*tile_Size, tile_Size), "P": (5*tile_Size, tile_Size)
}

pieceValueDict = {
    chess.KING: 20000,
    chess.QUEEN: 900,
    chess.ROOK: 500,
    chess.BISHOP: 330,
    chess.KNIGHT: 320,
    chess.PAWN: 100
}

columnLetters = ["a", "b", "c", "d", "e", "f", "g", "h"]

# ─── Version-compatible board hashing ────────────────────────────────────────
# zobrist_hash() was added in python-chess 1.x; _transposition_key() exists in
# older builds. Fall back to a fast FEN-based key if neither is present.
def board_key():
    if hasattr(board, 'zobrist_hash'):
        return board.zobrist_hash()
    elif hasattr(board, '_transposition_key'):
        return board._transposition_key()
    else:
        # FEN without move counters (positions that differ only in clock are
        # treated as the same node, which is fine for the TT)
        return ' '.join(board.fen().split()[:4])

# ─── Piece-Square Tables (from white's perspective, a1=index 0) ───────────────
# These are standard tables used in strong open-source engines

pawnvalues = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-20,-20, 10, 10,  5,
     5, -5,-10,  0,  0,-10, -5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0
]

knightvalues = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

bishopvalues = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

rookvalues = [
     0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

queenvalues = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -10,  5,  5,  5,  5,  5,  0,-10,
      0,  0,  5,  5,  5,  5,  0, -5,
     -5,  0,  5,  5,  5,  5,  0, -5,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

# King middlegame: stay safe, castle
kingvalues_mid = [
     20, 30, 10,  0,  0, 10, 30, 20,
     20, 20,  0,  0,  0,  0, 20, 20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30
]

# King endgame: centralise
kingvalues_end = [
    -50,-30,-30,-30,-30,-30,-30,-50,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -50,-40,-30,-20,-20,-30,-40,-50
]

locationValuesDict = {
    chess.PAWN:   pawnvalues,
    chess.KNIGHT: knightvalues,
    chess.BISHOP: bishopvalues,
    chess.ROOK:   rookvalues,
    chess.QUEEN:  queenvalues,
    chess.KING:   kingvalues_mid   # swapped to endgame table when few pieces remain
}

# ─── Transposition Table ──────────────────────────────────────────────────────
# Flags used to record the type of the stored score
TT_EXACT = 0
TT_LOWER = 1   # alpha (lower bound)
TT_UPPER = 2   # beta  (upper bound)
TT_MAX_SIZE = 1_000_000

class TranspositionTable:
    """Fixed-capacity LRU transposition table using an OrderedDict."""
    def __init__(self, max_size=TT_MAX_SIZE):
        self.table = OrderedDict()
        self.max_size = max_size
        self.hits = 0

    def get(self, key):
        entry = self.table.get(key)
        if entry:
            self.hits += 1
            self.table.move_to_end(key)
        return entry

    def put(self, key, depth, score, flag, best_move):
        if key in self.table:
            existing = self.table[key]
            # Only overwrite if new search is at least as deep
            if existing[0] > depth:
                return
            self.table.move_to_end(key)
        else:
            if len(self.table) >= self.max_size:
                self.table.popitem(last=False)
        self.table[key] = (depth, score, flag, best_move)

    def clear(self):
        self.table.clear()
        self.hits = 0

tt = TranspositionTable()

# ─── Killer Move Heuristic ────────────────────────────────────────────────────
# Stores two quiet moves per depth that caused a beta cutoff
MAX_DEPTH = 10
killer_moves = [[None, None] for _ in range(MAX_DEPTH + 1)]

def store_killer(move, depth):
    if depth < MAX_DEPTH:
        if move != killer_moves[depth][0]:
            killer_moves[depth][1] = killer_moves[depth][0]
            killer_moves[depth][0] = move

def clear_killers():
    global killer_moves
    killer_moves = [[None, None] for _ in range(MAX_DEPTH + 1)]

# ─── History Heuristic ───────────────────────────────────────────────────────
# Tracks how often a move (from_sq, to_sq) caused a cutoff across the search
history_table = {}

def update_history(move, depth):
    key = (move.from_square, move.to_square)
    history_table[key] = history_table.get(key, 0) + depth * depth

def clear_history():
    history_table.clear()

# ─── Piece value lookup helpers ───────────────────────────────────────────────
def piece_value(piece_type):
    return pieceValueDict.get(piece_type, 0)

def is_endgame():
    """True when both sides have little material (no queens, or queen + ≤1 minor each)."""
    queens = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))
    if queens == 0:
        return True
    if queens == 2:
        white_minor = len(board.pieces(chess.ROOK, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.WHITE)) + len(board.pieces(chess.KNIGHT, chess.WHITE))
        black_minor = len(board.pieces(chess.ROOK, chess.BLACK)) + len(board.pieces(chess.BISHOP, chess.BLACK)) + len(board.pieces(chess.KNIGHT, chess.BLACK))
        if white_minor <= 1 and black_minor <= 1:
            return True
    return False

# ─── Move Ordering ────────────────────────────────────────────────────────────
def score_move(move, depth):
    """Higher score = search this move first."""
    score = 0

    # 1. Transposition table best move gets top priority
    tt_entry = tt.get(board_key())
    if tt_entry and tt_entry[3] == move:
        return 1_000_000

    # 2. Captures scored by MVV-LVA (Most Valuable Victim – Least Valuable Attacker)
    if board.is_capture(move):
        victim = board.piece_at(move.to_square)
        attacker = board.piece_at(move.from_square)
        victim_val  = piece_value(victim.piece_type)  if victim  else 0
        attacker_val = piece_value(attacker.piece_type) if attacker else 0
        score += 100_000 + victim_val * 10 - attacker_val

    # 3. Promotions
    if move.promotion:
        score += 90_000 + piece_value(move.promotion)

    # 4. Killer moves (quiet moves that previously caused beta cutoffs at this depth)
    if depth < MAX_DEPTH:
        if move == killer_moves[depth][0]:
            score += 80_000
        elif move == killer_moves[depth][1]:
            score += 70_000

    # 5. Castling bonus
    if board.is_castling(move):
        score += 60_000

    # 6. History heuristic for quiet moves
    key = (move.from_square, move.to_square)
    score += history_table.get(key, 0)

    return score

def ordered_moves(depth):
    moves = list(board.legal_moves)
    moves.sort(key=lambda m: score_move(m, depth), reverse=True)
    return moves

# ─── Static Exchange Evaluation (SEE) ────────────────────────────────────────
def see(square, attacker_colour):
    """
    Simplified SEE: returns the expected material gain from capturing on `square`
    with `attacker_colour` to move. Used in quiescence to skip losing captures.
    """
    value = 0
    attacker_sq = None
    min_attacker_val = 99999
    for sq in board.attackers(attacker_colour, square):
        p = board.piece_at(sq)
        if p and piece_value(p.piece_type) < min_attacker_val:
            min_attacker_val = piece_value(p.piece_type)
            attacker_sq = sq
    if attacker_sq is None:
        return 0
    target = board.piece_at(square)
    target_val = piece_value(target.piece_type) if target else 0
    board.push(chess.Move(attacker_sq, square))
    value = max(0, target_val - see(square, not attacker_colour))
    board.pop()
    return value

# ─── Board Evaluation ─────────────────────────────────────────────────────────
def BoardEval(colour):
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    if board.is_checkmate():
        # Current side to move is in checkmate, so colour just moved and won
        if board.turn == colour:
            return -99999
        else:
            return 99999

    endgame = is_endgame()
    king_table = kingvalues_end if endgame else kingvalues_mid

    score = 0

    # Mobility bonus: more legal moves = better position
    if board.turn == colour:
        score += len(list(board.legal_moves)) * 2
    else:
        score -= len(list(board.legal_moves)) * 2

    for piece_type in pieceValueDict:
        val = pieceValueDict[piece_type]
        loc_table = king_table if piece_type == chess.KING else locationValuesDict[piece_type]

        for sq in board.pieces(piece_type, colour):
            idx = chess.square_mirror(sq) if colour == chess.BLACK else sq
            score += val + loc_table[idx]

            # Bonus: rooks on open / semi-open files
            if piece_type == chess.ROOK:
                file = chess.square_file(sq)
                file_squares = chess.SquareSet(chess.BB_FILES[file])
                pawns_on_file = (len(board.pieces(chess.PAWN, chess.WHITE) & file_squares) +
                                 len(board.pieces(chess.PAWN, chess.BLACK) & file_squares))
                if pawns_on_file == 0:
                    score += 20   # open file
                elif pawns_on_file == 1:
                    score += 10   # semi-open

            # Bonus: bishop pair
            if piece_type == chess.BISHOP:
                if len(board.pieces(chess.BISHOP, colour)) >= 2:
                    score += 15

            # Passed pawn bonus
            if piece_type == chess.PAWN:
                file = chess.square_file(sq)
                rank = chess.square_rank(sq)
                enemy_pawns = board.pieces(chess.PAWN, not colour)
                ahead = range(rank + 1, 8) if colour == chess.WHITE else range(rank - 1, -1, -1)
                is_passed = not any(
                    chess.square(f, r) in enemy_pawns
                    for f in [file - 1, file, file + 1] if 0 <= f <= 7
                    for r in ahead
                )
                if is_passed:
                    bonus = rank if colour == chess.WHITE else (7 - rank)
                    score += 20 + bonus * 5

        for sq in board.pieces(piece_type, not colour):
            idx = chess.square_mirror(sq) if colour == chess.WHITE else sq
            score -= val + loc_table[idx]

            if piece_type == chess.ROOK:
                file = chess.square_file(sq)
                file_squares = chess.SquareSet(chess.BB_FILES[file])
                pawns_on_file = (len(board.pieces(chess.PAWN, chess.WHITE) & file_squares) +
                                 len(board.pieces(chess.PAWN, chess.BLACK) & file_squares))
                if pawns_on_file == 0:
                    score -= 20
                elif pawns_on_file == 1:
                    score -= 10

            if piece_type == chess.BISHOP:
                if len(board.pieces(chess.BISHOP, not colour)) >= 2:
                    score -= 15

            if piece_type == chess.PAWN:
                file = chess.square_file(sq)
                rank = chess.square_rank(sq)
                opp = not colour
                friendly_pawns = board.pieces(chess.PAWN, colour)
                ahead = range(rank + 1, 8) if opp == chess.WHITE else range(rank - 1, -1, -1)
                is_passed = not any(
                    chess.square(f, r) in friendly_pawns
                    for f in [file - 1, file, file + 1] if 0 <= f <= 7
                    for r in ahead
                )
                if is_passed:
                    bonus = rank if opp == chess.WHITE else (7 - rank)
                    score -= 20 + bonus * 5

    return score

# ─── Quiescence Search ───────────────────────────────────────────────────────
def quiescence(colour, alpha, beta, depth=0):
    """Search only captures until a quiet position to avoid horizon effect."""
    stand_pat = BoardEval(colour)

    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat

    # Only look at captures; order them by MVV-LVA
    captures = [m for m in board.legal_moves if board.is_capture(m)]
    captures.sort(key=lambda m: score_move(m, 0), reverse=True)

    for move in captures:
        # Delta pruning: skip if even capturing the most valuable piece can't improve alpha
        victim = board.piece_at(move.to_square)
        if victim:
            if stand_pat + piece_value(victim.piece_type) + 200 < alpha:
                continue  # futility

        board.push(move)
        score = -quiescence(not colour, -beta, -alpha, depth + 1)
        board.pop()

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha

# ─── Negamax with Alpha-Beta, TT, Null Move, LMR ─────────────────────────────
NULL_MOVE_REDUCTION = 3   # R value for null-move pruning
LMR_FULL_DEPTH_MOVES = 4  # Search this many moves at full depth before reducing

def negamax(depth, alpha, beta, colour, ply=0, allow_null=True):
    """
    Negamax formulation: score is always from the perspective of `colour`.
    Returns (score, best_move).
    """
    alpha_orig = alpha

    # ── Transposition table lookup ────────────────────────────────────────────
    tt_key = board_key()
    tt_entry = tt.get(tt_key)
    if tt_entry and tt_entry[0] >= depth:
        tt_depth, tt_score, tt_flag, tt_move = tt_entry
        if tt_flag == TT_EXACT:
            return tt_score, tt_move
        elif tt_flag == TT_LOWER:
            alpha = max(alpha, tt_score)
        elif tt_flag == TT_UPPER:
            beta = min(beta, tt_score)
        if alpha >= beta:
            return tt_score, tt_move

    # ── Terminal nodes ────────────────────────────────────────────────────────
    if board.is_game_over():
        return BoardEval(colour), None
    if depth == 0:
        return quiescence(colour, alpha, beta), None

    # ── Null-move pruning ─────────────────────────────────────────────────────
    # If giving the opponent a free move doesn't improve their position beyond beta,
    # we can prune. Skip in endgame (zugzwang risk) and when in check.
    if (allow_null and depth >= NULL_MOVE_REDUCTION + 1
            and not board.is_check() and not is_endgame()):
        board.push(chess.Move.null())
        null_score, _ = negamax(depth - 1 - NULL_MOVE_REDUCTION,
                                -beta, -beta + 1, not colour, ply + 1, allow_null=False)
        null_score = -null_score
        board.pop()
        if null_score >= beta:
            return beta, None

    # ── Futility pruning ─────────────────────────────────────────────────────
    # At frontier nodes, skip moves that can't possibly raise alpha
    futility_margin = [0, 200, 500]
    if (depth <= 2 and not board.is_check()
            and abs(alpha) < 90000 and abs(beta) < 90000):
        static = BoardEval(colour)
        if static + futility_margin[depth] <= alpha:
            return quiescence(colour, alpha, beta), None

    # ── Main move loop ────────────────────────────────────────────────────────
    moves = ordered_moves(ply)
    best_move = None
    best_score = -9_999_999
    moves_searched = 0

    for move in moves:
        is_capture = board.is_capture(move)   # must check BEFORE push
        board.push(move)
        is_check = board.is_check()

        # ── Late Move Reductions (LMR) ────────────────────────────────────────
        # After the first few moves, reduce depth for quiet non-checking moves
        reduction = 0
        if (moves_searched >= LMR_FULL_DEPTH_MOVES
                and depth >= 3
                and not is_capture
                and not is_check
                and not move.promotion):
            reduction = 1
            if moves_searched >= LMR_FULL_DEPTH_MOVES * 2:
                reduction = 2

        # Search with possible reduction, re-search at full depth if it raises alpha
        score, _ = negamax(depth - 1 - reduction,
                           -beta, -alpha, not colour, ply + 1)
        score = -score

        if reduction > 0 and score > alpha:
            # Re-search at full depth
            score, _ = negamax(depth - 1, -beta, -alpha, not colour, ply + 1)
            score = -score

        board.pop()
        moves_searched += 1

        if score > best_score:
            best_score = score
            best_move = move

        alpha = max(alpha, score)

        if alpha >= beta:
            # Beta cutoff
            if not is_capture:
                store_killer(move, ply)
                update_history(move, depth)
            break

    # ── Store result in transposition table ───────────────────────────────────
    if best_score <= alpha_orig:
        flag = TT_UPPER
    elif best_score >= beta:
        flag = TT_LOWER
    else:
        flag = TT_EXACT
    tt.put(tt_key, depth, best_score, flag, best_move)

    return best_score, best_move

# ─── Iterative Deepening ──────────────────────────────────────────────────────
def DoAIMoveMinimax(max_depth, time_limit=5.0):
    """
    Iterative deepening with time management.
    Searches depth 1 → max_depth, stopping early if time_limit is exceeded.
    """
    tt.clear()
    clear_killers()
    clear_history()

    start = time.time()
    best_move = None

    for depth in range(1, max_depth + 1):
        # Aspiration windows: search a narrow window first, widen on failure
        alpha, beta = -9_999_999, 9_999_999
        if depth >= 4 and best_move is not None:
            window = 50
            alpha = max(-9_999_999, last_score - window)
            beta  = min( 9_999_999, last_score + window)

        while True:
            score, move = negamax(depth, alpha, beta, aiColour)
            if score <= alpha:
                alpha = max(-9_999_999, alpha - window * 4)
            elif score >= beta:
                beta = min(9_999_999, beta + window * 4)
            else:
                break  # Score inside window

        last_score = score
        if move is not None:
            best_move = move

        elapsed = time.time() - start
        if elapsed >= time_limit:
            break

        # Stop searching if checkmate found
        if abs(score) > 90000:
            break

    return best_move

# ─────────────────────────────────────────────────────────────────────────────
# Everything below is unchanged from the original (graphics / UI code)
# ─────────────────────────────────────────────────────────────────────────────

board = chess.Board()

playerColour = None
aiColour = None
flipBoard = None
tileSelected = None
aiMove = None
possibleMoves = None
playerResigned = False
moveHistory = []

def ResetGame():
    board.reset()
    global playerColour
    playerColour = random.choice([chess.WHITE, chess.BLACK])

    if debug:
        board.set_fen(debug_fen)
        playerColour = debug_playerColour

    global aiColour
    aiColour = not playerColour
    global flipBoard
    flipBoard = playerColour == chess.BLACK
    global tileSelected
    tileSelected = None
    global possibleMoves
    possibleMoves = []
    global aiMove
    aiMove = None
    global playerResigned
    playerResigned = False
    global moveHistory
    moveHistory = []
    UpdateHistorySurface()

scr_Width  = 1200 * scale_factor
scr_Height = 1000 * scale_factor
displaySurface = pygame.display.set_mode((scr_Width, scr_Height), 0, 32)
historySurface = pygame.Surface((board_Size, scr_Height - board_Size - boardOffset * 3))
historyFont = pygame.font.Font(asset_path("assets/font/Roboto-Regular.ttf"), 14)

def load_scaled_image(path, scale_factor):
    image = pygame.image.load(asset_path(path))
    new_width  = int(image.get_width()  * scale_factor)
    new_height = int(image.get_height() * scale_factor)
    return pygame.transform.scale(image, (new_width, new_height))

drawScreen    = load_scaled_image("assets/drawscreen.png",   scale_factor)
victoryScreen = load_scaled_image("assets/victoryscreen.png", scale_factor)
defeatScreen  = load_scaled_image("assets/defeatscreen.png",  scale_factor)
boardCat      = load_scaled_image("assets/cat.png",           scale_factor)
resignImage   = load_scaled_image("assets/resign.png",        scale_factor)
playAgainImage= load_scaled_image("assets/playagain.png",     scale_factor)

playAgainRect = playAgainImage.get_rect()
playAgainRect[0] = board_Size + boardOffset * 2
playAgainRect[1] = board_Size * 0.4 + boardOffset

def UpdateHistorySurface():
    historySurface.fill((128, 128, 128))
    moveNumber = 0
    even = True
    x = 0
    y = 0
    for move in moveHistory:
        fontColour = (255, 255, 255) if even else (0, 0, 0)
        if not even:
            x += 50
        tempMoveSurface = historyFont.render(move, True, fontColour)
        historySurface.blit(tempMoveSurface, (x, y))
        if not even:
            y += 25
            x -= 50
        even = not even
        moveNumber += 1
        if moveNumber == 14:
            moveNumber = 0
            x += 100
            y = 0

def CreateChessBoardSurface():
    surface = pygame.Surface((board_Size, board_Size))
    surface.fill((80, 80, 80))
    for j in range(0, 8):
        for i in [0, 2, 4, 6]:
            if j % 2 == 1:
                i += 1
            pygame.draw.rect(surface, (192, 192, 192), (i*tile_Size, j*tile_Size, tile_Size, tile_Size))
    return surface

boardSurface = CreateChessBoardSurface()

def CreateHighlightSurface(colour):
    surface = pygame.Surface((tile_Size, tile_Size))
    surface.set_alpha(128)
    surface.fill(colour)
    return surface

highlightSurface   = CreateHighlightSurface((255, 255, 102))
selectedSurface    = CreateHighlightSurface((32, 178, 170))
aiHighlightSurface = CreateHighlightSurface((255, 51, 51))

logo      = load_scaled_image("assets/logo.png",      scale_factor)
titleText = load_scaled_image("assets/titletext.png", scale_factor)

def CreateImagesForPieces():
    image = load_scaled_image("assets/chess.png", scale_factor)
    return pygame.transform.scale(image, (450, 150))

piecesImage = CreateImagesForPieces()

def GetTileFromPosition(position, flipBoard):
    i = position[0] - boardOffset
    j = position[1] - boardOffset
    if i < 0 or j < 0:
        return None
    elif i >= board_Size or j >= board_Size:
        return None
    i = int(i / tile_Size)
    j = int(j / tile_Size)
    j = 8 - j
    if flipBoard:
        i = 7 - i
        j = 9 - j
    return columnLetters[i] + str(j)

def DrawVictoryScreen():
    displaySurface.blit(playAgainImage, (playAgainRect[0], playAgainRect[1]))
    outcome = board.outcome()
    if playerResigned:
        displaySurface.blit(defeatScreen, (board_Size + boardOffset * 2, boardOffset))
    else:
        if outcome.winner == playerColour:
            displaySurface.blit(victoryScreen, (board_Size + boardOffset * 2, boardOffset))
        elif outcome.winner is None:
            displaySurface.blit(drawScreen, (board_Size + boardOffset * 2, boardOffset))
        else:
            displaySurface.blit(defeatScreen, (board_Size + boardOffset * 2, boardOffset))

def HighLightSquare(tile, flipBoard, surface):
    row    = int(tile[1]) - 1
    column = columnLetters.index(tile[0])
    if flipBoard:
        column = 7 - column
    else:
        row = 7 - row
    i = column * tile_Size + boardOffset
    j = row    * tile_Size + boardOffset
    displaySurface.blit(surface, (i, j))

def OnMouseButtonUp(mousePosition):
    global playerResigned
    if not board.is_game_over() and not playerResigned:
        tileClicked = GetTileFromPosition(mousePosition, flipBoard)
        global possibleMoves, tileSelected
        if board.turn == playerColour:
            if tileClicked is None:
                tileSelected = None
                possibleMoves = []
                if playAgainRect.collidepoint(mousePosition):
                    playerResigned = True
            else:
                square = chess.parse_square(tileClicked)
                pieceAtSquare = board.piece_at(square)
                if pieceAtSquare is not None and pieceAtSquare.color == playerColour:
                    tileSelected = tileClicked
                    legal_moves = list(board.legal_moves)
                    possibleMoves = [m for m in legal_moves if m.from_square == square]
                else:
                    for move in possibleMoves:
                        if move.to_square == square:
                            moveHistory.append(board.san(move))
                            board.push(move)
                            UpdateHistorySurface()
                            global aiMove
                            aiMove = None
                            break
                    tileSelected = None
                    possibleMoves = []
    else:
        if playAgainRect.collidepoint(mousePosition):
            ResetGame()

ResetGame()
running   = True
startGame = False

while not startGame and running:
    displaySurface.fill((255, 255, 255))
    logoWidth, logoHeight = logo.get_width(), logo.get_height()
    displaySurface.blit(logo, ((scr_Width/2) - (logoWidth/2),
                               (scr_Height/2) - (logoHeight/2)))
    titleTextWidth, titleTextHeight = titleText.get_width(), titleText.get_height()
    displaySurface.blit(titleText, ((scr_Width/2) - (titleTextWidth/2),
                                    (scr_Height/2) - (titleTextHeight/2) + (logoHeight*1.5)/2))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONUP:
            startGame = True
    pygame.display.flip()

while running:
    if not board.is_game_over() and not playerResigned:
        if board.turn != playerColour:
            move = DoAIMoveMinimax(max_depth=6, time_limit=5.0)
            if move is not None:
                aiMove = move.uci()
                moveHistory.append(board.san(move))
                board.push(move)
                UpdateHistorySurface()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONUP:
            OnMouseButtonUp(pygame.mouse.get_pos())

    displaySurface.fill((128, 128, 128))
    displaySurface.blit(boardCat,      (board_Size - 45, board_Size / 2))
    displaySurface.blit(historySurface,(boardOffset, board_Size + boardOffset * 2))
    displaySurface.blit(boardSurface,  (boardOffset, boardOffset))
    displaySurface.blit(resignImage,   (playAgainRect[0], playAgainRect[1]))

    if tileSelected is not None:
        HighLightSquare(tileSelected, flipBoard, selectedSurface)
        for move in possibleMoves:
            HighLightSquare(move.uci()[2:4], flipBoard, highlightSurface)

    if aiMove is not None:
        HighLightSquare(aiMove[2:4], flipBoard, aiHighlightSurface)
        HighLightSquare(aiMove[0:2], flipBoard, aiHighlightSurface)

    piece_map = board.piece_map()
    for index in piece_map:
        i = index % 8
        j = int(index / 8)
        if flipBoard:
            i = 7 - i
        else:
            j = 7 - j
        piece  = piece_map[index]
        symbol = piece.symbol()
        position = (boardOffset + i*tile_Size, boardOffset + j*tile_Size)
        area = piecepositionDict[symbol] + (tile_Size, tile_Size)
        displaySurface.blit(piecesImage, position, area=area)

    if board.is_game_over() or playerResigned:
        DrawVictoryScreen()

    pygame.display.flip()

pygame.font.quit()
pygame.quit()
