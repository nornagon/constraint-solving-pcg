import random
import os

# or-tools is Google's open-source constraint solving library:
# https://developers.google.com/optimization/
from ortools.sat.python import cp_model
from PIL import Image

model = cp_model.CpModel()

# Number of tiles in X & Y directions in the map
width = 20
height = 20

# Each of the three types of terrain will be associated with an integer (0 for
# rock, 1 for water, 2 for grass).
TERRAIN = ['rock', 'water', 'grass']
# ITERRAIN maps the name of the terrain to the number that represents it.
ITERRAIN = {t: i for i, t in enumerate(TERRAIN)}

# Each element of the 'tiles' array will be an integer variable corresponding
# to a tile on the map, allowing the solver to pick what terrain goes there.
tiles = []
for y in range(height):
  for x in range(width):
    tiles.append(model.NewIntVar(0, len(TERRAIN) - 1, f'[{x},{y}]'))

# For each horizontally adjacent pair of tiles, we're going to forbid the
# solver from choosing that one of them is rock and the other is water. We'll
# do the same for vertically adjacent pairs of tiles. This will prevent the
# solver from putting water directly adjacent to rock.
for y in range(height):
  for x in range(width - 1):
    model.AddForbiddenAssignments(
        [tiles[y * width + x], tiles[y * width + x + 1]],
        [[ITERRAIN['rock'], ITERRAIN['water']], [ITERRAIN['water'], ITERRAIN['rock']]])
for x in range(width):
  for y in range(height - 1):
    model.AddForbiddenAssignments(
        [tiles[y * width + x], tiles[(y + 1) * width + x]],
        [[ITERRAIN['rock'], ITERRAIN['water']], [ITERRAIN['water'], ITERRAIN['rock']]])

# We're going to require that the amount of water on the map is between
# 25% and 50% of the tiles. To do that, we'll create a boolean variable (that
# can just be 0 or 1) for each (tile, terrain type) pair.
domain_map = [[model.NewBoolVar(f'tile {i} == {k}') for k in range(len(TERRAIN))] for i in tiles]
# Then we'll tell the solver to enforce the constraint that if the tile has a
# particular terrain type, then the relevant boolean variables in domain_map
# will be correct: domain_map[tile_index][terrain_type] will be true if that
# tile is set to that terrain type, and false otherwise. Without this
# constraint, the boolean variables would be totally disconnected from the
# integer variables.
for i in range(len(tiles)):
  model.AddMapDomain(tiles[i], domain_map[i])
# Finally, we're going to count up how many of the water-type boolean variables
# are set to true. Since each boolean variable is 0 or 1, if we add them all
# together we'll get a count of how many are true.
num_water_tiles = cp_model.LinearExpr.Sum([domain_map[i][ITERRAIN['water']] for i in range(len(tiles))])
# And now we can add the constraint we want: that the number of water tiles
# must be bigger than 25% of the map size, and smaller than 50%.
model.Add(num_water_tiles >= width*height//4)
model.Add(num_water_tiles <= width*height//2)

# Before we tell the solver to generate a map for us, we're going to give it a
# random map to start with. This randomly generated hint doesn't obey any of
# our constraints--it'll have water next to rock and isn't guaranteed to have
# the right amount of water--but it'll give the solver a random place to start,
# so it won't generate a boring map that's all grass.
for y in range(height):
  for x in range(width):
    model.AddHint(tiles[y * width + x], random.randint(0, len(TERRAIN) - 1))

# We're ready to generate a map!
solver = cp_model.CpSolver()
status = solver.Solve(model)
if status == cp_model.FEASIBLE:
  # We're going to generate a PNG file with our map, but if this was your game
  # you could use the data any way you want. The key function for extracting
  # data is used in the loop below: solver.Value(some_variable).
  tile_sheet = Image.open(os.path.join(os.path.dirname(__file__), 'tiles.png'))
  sz = 64
  map_image = Image.new(tile_sheet.mode, (sz * width, sz * height))
  def tile_at(x, y):
    return tile_sheet.crop((x*sz, y*sz, x*sz+sz, y*sz+sz))
  tile_sub = {
    'grass': tile_at(1, 1),
    'rock': tile_at(6, 1),
    'water': tile_at(11, 1),
  }
  for y in range(height):
    for x in range(width):
      terrain_type = solver.Value(tiles[y * width + x])
      map_image.paste(tile_sub[TERRAIN[terrain_type]],
          (x*sz, y*sz, x*sz+sz, y*sz+sz))
  map_image.save('out.png', 'PNG')
else:
  raise Exception("Model was unsolvable")
