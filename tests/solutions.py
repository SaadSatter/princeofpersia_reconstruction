"""Hand-written winning routes, used only by tests to prove each situation is
solvable. Never shown to any player."""

SOLUTIONS = {
    "S1": ["RIGHT", "RIGHT", "JUMP_RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT",
           "RIGHT", "RIGHT", "RUN_JUMP_RIGHT", "RIGHT", "UP"],
    "S2": ["RIGHT", "RIGHT", "RIGHT", "STEP_RIGHT", "STEP_RIGHT", "STEP_RIGHT",
           "STEP_RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "JUMP_RIGHT",
           "RIGHT", "RIGHT", "RIGHT", "UP"],
    "S3": ["RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT",          # drop into row 1
           "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT",          # to room 2 col 1
           "JUMP_RIGHT", "JUMP_RIGHT", "RIGHT", "RIGHT", "RIGHT",  # room 3 col 0
           "RIGHT", "RIGHT", "RIGHT", "RIGHT",                   # plate, to col 4
           "STEP_RIGHT", "STEP_RIGHT", "STEP_RIGHT",             # spikes
           "RIGHT", "RIGHT", "RIGHT", "RIGHT",                   # gate, room 4 col 1
           "LEFT", "UP", "RIGHT", "RIGHT",                       # climb, plate, drop
           "RIGHT", "RIGHT", "RIGHT", "WAIT", "WAIT", "WAIT", "WAIT", "UP"],
    "H1": ["LEFT", "LEFT", "LEFT", "JUMP_LEFT", "LEFT", "LEFT", "LEFT", "LEFT",
           "LEFT", "RUN_JUMP_LEFT", "UP"],
    "H2": ["RIGHT", "RIGHT", "RIGHT", "STEP_RIGHT", "STEP_RIGHT", "STEP_RIGHT",
           "JUMP_RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT",
           "STEP_RIGHT", "STEP_RIGHT", "RIGHT", "UP"],
    "H3": ["RIGHT"] * 8 +                                   # run over loose, drop to row 2
          ["RIGHT", "RIGHT", "JUMP_RIGHT", "RIGHT",           # room 2: pit, plate
           "STEP_RIGHT", "STEP_RIGHT", "STEP_RIGHT",          # spikes
           "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT",       # room 3 col 2
           "UP", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT", "RIGHT",  # gate, room 4
           "RIGHT", "RIGHT", "RIGHT", "RIGHT", "JUMP_RIGHT", "UP",              # ledge plate
           "LEFT", "DOWN", "DOWN", "LEFT", "LEFT", "LEFT",    # hang, drop, fall to exit
           "WAIT", "WAIT", "WAIT", "UP"],
}
