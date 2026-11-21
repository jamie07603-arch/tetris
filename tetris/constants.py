"""Tunable gameplay constants shared by the logic and presentation layers.

Everything in this module is pure data: importing it must never require Pygame.
"""

# --- Playfield -------------------------------------------------------------

COLS = 10
VISIBLE_ROWS = 20

# --- Gravity / level curve -------------------------------------------------

BASE_GRAVITY = 0.8  # Seconds per cell at level 1.
GRAVITY_FACTOR = 0.85  # Gravity interval multiplier applied per level.
MIN_GRAVITY = 0.05  # Fastest allowed gravity interval, in seconds.
LINES_PER_LEVEL = 10

# --- Locking ---------------------------------------------------------------

LOCK_DELAY = 0.5  # Seconds a grounded piece waits before locking.
MAX_LOCK_RESETS = 15  # Caps how often moving/rotating can restart the timer.

# --- Scoring ---------------------------------------------------------------

# Points per line-clear count (index = lines cleared), multiplied by the level
# the clear happened at.
LINE_SCORES = (0, 100, 300, 500, 800)
SOFT_DROP_POINTS = 1  # Per cell moved down by the player.
HARD_DROP_POINTS = 2  # Per cell moved down by a hard drop.

# --- Timing ----------------------------------------------------------------

FPS = 60
FIXED_TIMESTEP = 1.0 / 60.0
# Input repeat delays, in seconds. DAS = delayed auto shift, ARR = auto repeat
# rate; both drive horizontal movement while a direction key is held.
DAS = 0.17
ARR = 0.05
SOFT_DROP_REPEAT = 0.05
MAX_FRAME_TIME = 0.25  # Prevents a huge fixed-update catch-up after a stall.
