sizes = [20, 50, 100, 200, 500, 1000, 10000, 20000, 50000, 100000, 200000, 500000, 1000000]

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
  return level_map
