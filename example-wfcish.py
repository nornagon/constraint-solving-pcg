"""
This is an example of using a constraint solver to generate maps in a way
that's similar to [Wave Function Collapse][].

[Wave Function Collapse]: https://github.com/mxgmn/WaveFunctionCollapse
"""
import random
import os

# or-tools is Google's open-source constraint solving library:
# https://developers.google.com/optimization/
from ortools.sat.python import cp_model
from PIL import Image

model = cp_model.CpModel()

width = 20
height = 20

# Each element of this array is a tuple with two values:
#  - The coordinates into the spritesheet for the tile it's describing
#  - An object describing what the edges of that tile look like.
# Each edge object has four keys: 'u'p, 'd'own, 'l'eft and 'r'ight.
# The values in the edge objects describe what that edge looks like at the
# corner, the middle, and the other corner. So for example, the value 'rgg'
# means 'rock', 'grass', 'grass'. So a corner tile would be labeled like this:
#
#   r   r   r
#  +---------+
# r|rrrrrrrrr|r
#  |rgggggggg|
# r|rgggggggg|g
#  |rgggggggg|
# r|rgggggggg|g
#  +---------+
#   r   g   g
#
# For a complete edge object of { 'u': 'rrr', 'd': 'rgg', 'l': 'rrr', 'r': 'rgg'}
TILES = [
  ((1, 1), { 'u': 'ggg', 'd': 'ggg', 'l': 'ggg', 'r': 'ggg' }),
  ((0, 0), { 'u': 'rrr', 'd': 'rgg', 'l': 'rrr', 'r': 'rgg' }),
  ((1, 0), { 'u': 'rrr', 'd': 'ggg', 'l': 'rgg', 'r': 'rgg' }),
  ((2, 0), { 'u': 'rrr', 'd': 'ggr', 'l': 'rgg', 'r': 'rrr' }),
  ((0, 1), { 'u': 'rgg', 'd': 'rgg', 'l': 'rrr', 'r': 'ggg' }),
  ((2, 1), { 'u': 'ggr', 'd': 'ggr', 'l': 'ggg', 'r': 'rrr' }),
  ((0, 2), { 'u': 'rgg', 'd': 'rrr', 'l': 'rrr', 'r': 'ggr' }),
  ((1, 2), { 'u': 'ggg', 'd': 'rrr', 'l': 'ggr', 'r': 'ggr' }),
  ((2, 2), { 'u': 'ggr', 'd': 'rrr', 'l': 'ggr', 'r': 'rrr' }),
  ((3, 0), { 'u': 'ggg', 'd': 'ggr', 'l': 'ggg', 'r': 'ggr' }),
  ((4, 0), { 'u': 'ggg', 'd': 'rgg', 'l': 'ggr', 'r': 'ggg' }),
  ((3, 1), { 'u': 'ggr', 'd': 'ggg', 'l': 'ggg', 'r': 'rgg' }),
  ((4, 1), { 'u': 'rgg', 'd': 'ggg', 'l': 'rgg', 'r': 'ggg' }),
  ((3, 2), { 'u': 'ggg', 'd': 'ggg', 'l': 'ggg', 'r': 'ggg' }),
  ((4, 2), { 'u': 'ggg', 'd': 'ggg', 'l': 'ggg', 'r': 'ggg' }),

  ((5, 0), { 'u': 'ggg', 'd': 'grr', 'l': 'ggg', 'r': 'grr' }),
  ((6, 0), { 'u': 'ggg', 'd': 'rrr', 'l': 'grr', 'r': 'grr' }),
  ((7, 0), { 'u': 'ggg', 'd': 'rrg', 'l': 'grr', 'r': 'ggg' }),
  ((5, 1), { 'u': 'grr', 'd': 'grr', 'l': 'ggg', 'r': 'rrr' }),
  ((6, 1), { 'u': 'rrr', 'd': 'rrr', 'l': 'rrr', 'r': 'rrr' }),
  ((7, 1), { 'u': 'rrg', 'd': 'rrg', 'l': 'rrr', 'r': 'ggg' }),
  ((5, 2), { 'u': 'grr', 'd': 'ggg', 'l': 'ggg', 'r': 'rrg' }),
  ((6, 2), { 'u': 'rrr', 'd': 'ggg', 'l': 'rrg', 'r': 'rrg' }),
  ((7, 2), { 'u': 'rrg', 'd': 'ggg', 'l': 'rrg', 'r': 'ggg' }),
  ((8, 0), { 'u': 'rrr', 'd': 'rrg', 'l': 'rrr', 'r': 'rrg' }),
  ((9, 0), { 'u': 'rrr', 'd': 'grr', 'l': 'rrg', 'r': 'rrr' }),
  ((8, 1), { 'u': 'rrg', 'd': 'rrr', 'l': 'rrr', 'r': 'grr' }),
  ((9, 1), { 'u': 'grr', 'd': 'rrr', 'l': 'grr', 'r': 'rrr' }),

  ((10, 0), { 'u': 'ggg', 'd': 'gww', 'l': 'ggg', 'r': 'gww' }),
  ((11, 0), { 'u': 'ggg', 'd': 'www', 'l': 'gww', 'r': 'gww' }),
  ((12, 0), { 'u': 'ggg', 'd': 'wwg', 'l': 'gww', 'r': 'ggg' }),
  ((10, 1), { 'u': 'gww', 'd': 'gww', 'l': 'ggg', 'r': 'www' }),
  ((11, 1), { 'u': 'www', 'd': 'www', 'l': 'www', 'r': 'www' }),
  ((12, 1), { 'u': 'wwg', 'd': 'wwg', 'l': 'www', 'r': 'ggg' }),
  ((10, 2), { 'u': 'gww', 'd': 'ggg', 'l': 'ggg', 'r': 'wwg' }),
  ((11, 2), { 'u': 'www', 'd': 'ggg', 'l': 'wwg', 'r': 'wwg' }),
  ((12, 2), { 'u': 'wwg', 'd': 'ggg', 'l': 'wwg', 'r': 'ggg' }),
  ((13, 0), { 'u': 'www', 'd': 'wwg', 'l': 'www', 'r': 'wwg' }),
  ((14, 0), { 'u': 'www', 'd': 'gww', 'l': 'wwg', 'r': 'www' }),
  ((13, 1), { 'u': 'wwg', 'd': 'www', 'l': 'www', 'r': 'gww' }),
  ((14, 1), { 'u': 'gww', 'd': 'www', 'l': 'gww', 'r': 'www' }),
]

tiles = []
for y in range(height):
  for x in range(width):
    tiles.append(model.NewIntVar(0, len(TILES) - 1, f'[{x},{y}]'))
    model.AddHint(tiles[y * width + x], random.randint(0, len(TILES) - 1))

# These constraints enforce that edges match when tiles are placed next to each
# other.
permitted_horizontal_pairs = []
for i in range(len(TILES)):
  for j in range(len(TILES)):
    if TILES[i][1]['r'] == TILES[j][1]['l']:
      permitted_horizontal_pairs.append([i, j])

permitted_vertical_pairs = []
for i in range(len(TILES)):
  for j in range(len(TILES)):
    if TILES[i][1]['d'] == TILES[j][1]['u']:
      permitted_vertical_pairs.append([i, j])

for y in range(height):
  for x in range(width - 1):
    model.AddAllowedAssignments(
        [tiles[y * width + x], tiles[y * width + x + 1]],
        permitted_horizontal_pairs)
for x in range(width):
  for y in range(height - 1):
    model.AddAllowedAssignments(
        [tiles[y * width + x], tiles[(y + 1) * width + x]],
        permitted_vertical_pairs)

water_vars = []
for y in range(height):
  for x in range(width):
    is_water = model.NewBoolVar(f'{x},{y} is water')
    # 32 is the all-water tile (not a corner).
    model.Add(tiles[y * width + x] == 32).OnlyEnforceIf(is_water)
    model.Add(tiles[y * width + x] != 32).OnlyEnforceIf(is_water.Not())
    water_vars.append(is_water)
s = cp_model.LinearExpr.Sum(water_vars)
model.Add(s >= width*height//4)
model.Add(s <= width*height//2)

solver = cp_model.CpSolver()
status = solver.Solve(model)
if status == cp_model.FEASIBLE:
  tile_sheet = Image.open(os.path.join(os.path.dirname(__file__), 'tiles.png'))
  sz = 64
  map_image = Image.new(tile_sheet.mode, (sz * width, sz * height))
  def tile_at(t):
    x, y = t
    return tile_sheet.crop((x*sz, y*sz, x*sz+sz, y*sz+sz))
  for y in range(height):
    for x in range(width):
      map_image.paste(tile_at(TILES[solver.Value(tiles[y * width + x])][0]),
          (x*sz, y*sz, x*sz+sz, y*sz+sz))
  map_image.save('out.png', 'PNG')
