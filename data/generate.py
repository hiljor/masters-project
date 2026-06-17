import math as math
TEST_SIZES = sizes = [round(math.sqrt(n)) for n in [100, 200, 500, 1000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000]]

""" 
Listing of levels and their parameters. 
Key is the level's string file name.
Value is a list of known parameters for the level, like (7, 34) meaning k=7 gives expected value 34.
"""
LEVELS = {
  "horse_arcs_170": [(12, 125)],
  "horse_diamonds_126":[(2,1),(7,39)],
  "horse_dots":[(8,11)],
  "horse_u-turn_128":[(8,41)],
  "horse_portals_cherries": [(8, 32)],
}

# pattern like this where k=8 gives best score:
# - ### ###
# -        
# - ### ###
# -        
# - ### ###
# -        
# - ### ###


def generate_size_test(size):
  mid = size // 2
  cols = [mid, mid + 2, mid - 2]
  rows = [mid]
  level_map = [["#" for _ in range(size)] for _ in range(size)]
  for i in range(size):
    for j in range(size):
      # clear the entire column or row marked for clearing
      if i in rows or j in cols:
        level_map[i][j] = " "
  # add horse
  level_map[mid][mid] = "H"
  
  # convert to list of strings
  level_map = ["".join(row) for row in level_map]
  return level_map
