from controller import Controller

from absl import app, flags
from scipy.interpolate import interp1d

import matplotlib as mpl
mpl.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import numpy as np

import sys

FLAGS = flags.FLAGS
flags.DEFINE_string("board_file", "boards/sample.txt", "Config file to build map.")
flags.DEFINE_string("log_file", "log.txt", "Log file to read movements.")

FLAGS(sys.argv)

# Parsing board file.
# NOTE: All (x, y) from here is plot-style (x, y), not array notation.

first_line = True
dim = None
booth_tiles = []
line_tiles = []
y = 0

fig = plt.figure(figsize=(8, 6))
ax = plt.axes(xlim=(0, 24), ylim=(0, 18))

with open(FLAGS.board_file, 'r') as config:
    for line in config:
        if first_line:
            f = line.split()
            dim = (int(f[1]), int(f[0]))
            n = int(f[2])
            booth_tiles  = [[] for _ in range(n)]
            line_tiles = [[] for _ in range(n)]
            first_line = False
        else:
            row = line.split()
            for x, tile in enumerate(row):
                if tile[0] == 'S' or tile[0] == 'M' or tile[0] == 'L':
                    i = int(tile[1:])
                    booth_tiles[i].append((x, y))
                elif tile[0] == 'E':
                    i = int(tile[1:])
                    line_tiles[i].insert(0, (y, x))
                elif tile[0] != 'F' and tile[0] != 'B':
                    i = int(tile)
                    line_tiles[i].append((y, x))
            y += 1

ax = plt.axes(xlim=(0, dim[0] * 3), ylim=(0, dim[1] * 3))

lines = []
directions = []

# Sorting each line to have proper ordering from start to end.
for i, line in enumerate(line_tiles):
    direction = "none"
    if len(line) > 1:
        sort_index = None
        rev = False

        end_loc = line[0]
        comp = line[1]
        if end_loc[0] == comp[0]:
            sort_index = 1
        else:
            sort_index = 0
        if end_loc[sort_index] < comp[sort_index]:
            rev = True

        if sort_index == 1 and rev:
            direction = "left"
        elif sort_index == 1 and not rev:
            direction = "right"
        elif sort_index == 0 and rev:
            direction = "up"
        else:
            direction = "down"

        new_tiles = sorted(line,
                           key=lambda x: x[sort_index],
                           reverse=rev)
        lines.append(new_tiles)
    directions.append(direction)

print("lines: {}".format(lines))
line_dic = {}

for n, line in enumerate(lines):
    for i, tile in enumerate(line):
        line_dic[tile] = (n, i)

# Creating rectangles to draw for each booth.
booth_rects = []
for booth in booth_tiles:
    lx, ly = booth[0]
    ux, uy = booth[-1]
    w, h = (ux - lx + 1) * 3, (uy - ly + 1) * 3
    booth_rects.append(plt.Rectangle((lx * 3, ly * 3), w, h, edgecolor='k', facecolor='#8b8989'))

# Parsing log file.

sec1 = True   # First section is # of bots
sec2 = False  # Second section is the names of the companies
sec3 = False  # Third section is the actual bot movements.

colors = ['#191970', '#b22222', '#eee9e9']

bots = []
company_names = []

time_step = 0

board = None

with open(FLAGS.log_file, 'r') as log:
    for line in log:
        if sec1:
            num_bots = [int(x) for x in line.split()]
            for i, n in enumerate(num_bots):
                team = [plt.Circle((0, 0), 0.3, edgecolor='k', 
                                   facecolor=colors[i]) for _ in range(n)]
                if team:
                    bots.append(team)
            sec1, sec2, sec3 = False, True, False
        elif sec2:
            controller = Controller(bots, dim, line_dic, directions)
            if line == "\n":
                sec1, sec2, sec3 = False, False, True
            else:
                company_names += line.split()
        elif sec3:
            bot_status = line.split()
            if len(bot_status) == 1:
                time_step = bot_status[0]
                controller.update(time_step)
            else:
                controller.parse_bot_state(bot_status)

test = controller.get_bot_positions(0, 0)
print("Asserted positions: {}".format(test))

prev_state = None
prev_tstep = None
is_none = False
prev_is_none = False

point_list = []
speeds = []
curr_points = []
curr_speeds = []
nones = []

max_tstep = 0
for tstep, loc in test.items():
    state = None
    if loc:
        state = (loc[1], loc[0])
    if tstep == 0:
        prev_state = state
        prev_tstep = tstep
        curr_points.append(prev_state)
        continue
    
    if state == None:
        if curr_points and not prev_is_none:
            point_list.append(curr_points)
            curr_points = [prev_state]
            prev_tstep = tstep
        if curr_speeds and not prev_is_none:
            speeds.append(curr_speeds)
            curr_speeds = []
        nones.append(tstep)
        prev_is_none = True
    else:
        curr_points.append(state)
        speed = tstep - prev_tstep
        curr_speeds.append(speed)

        prev_state = state
        prev_tstep = tstep
        prev_is_none = False
    
    max_tstep = tstep
if curr_points and not prev_is_none:
    point_list.append(curr_points)
if curr_speeds and not prev_is_none:
    speeds.append(curr_speeds)

BASE_SPEED = 50

print(nones)
print(point_list)
print(speeds)

total_points = []
for i, points in enumerate(point_list):
    if len(points) == 2:
        sample_space = BASE_SPEED * speeds[i][0]
        x1, y1 = points[0]
        x2, y2 = points[1]
        x_coords = np.linspace(x1, x2, sample_space, endpoint=False)
        y_coords = np.linspace(y1, y2, sample_space, endpoint=False)
        points = np.array([x_coords, y_coords]).T
        total_points.append(points)
        continue

    np_points = np.array(points)
    print(np_points)
    distance = np.cumsum(np.sqrt(np.sum(np.diff(np_points, axis=0)**2, axis=1)))
    distance = np.insert(distance, 0, 0)/distance[-1]
    print(distance)
    speed = np.array(speeds[i])
    alpha = np.array([])
    print(speed)

    for x in range(len(distance) - 1):
        new_section = np.linspace(distance[x], distance[x+1], BASE_SPEED * speed[x], endpoint=False)
        alpha = np.concatenate((alpha, new_section))
    
    interpolator = interp1d(distance, points, kind='quadratic', axis=0)
    np_points = interpolator(alpha)
    total_points.append(np_points)

print(total_points)
# Add in time where bot is still!
path = np.concatenate(total_points)

print("length of path: {}".format(len(path)))

    

points = np.array([[0.5, 1.5, 1.5, 2.5, 2.5],
                   [0.5, 0.5, 1.5, 1.5, 2.5]]).T  # a (nbre_points x nbre_dim) array

print(points)

print("Done defining points. Defining distances...")

# Linear length along the line:
distance = np.cumsum( np.sqrt(np.sum( np.diff(points, axis=0)**2, axis=1 )) )
print("Distance points: {}".format(distance))
distance = np.insert(distance, 0, 0)/distance[-1]
print("Scaled distance points: {}".format(distance))

print("Done defining distances. Creating interpolation...")

speed = np.array([2, 1, 2, 1])

alpha = np.array([])
for i in range(len(distance) - 1):
    end = False
    if i == len(distance) - 2:
        end = True
    new_section = np.linspace(distance[i], distance[i+1], 50 * speed[i] + (1 if end else 0), endpoint=end)
    alpha = np.concatenate((alpha, new_section))

interpolator = interp1d(distance, points, kind='quadratic', axis=0)
points = interpolator(alpha)

print("Created interpolation. Creating figure...")

patch = bots[0][0]

# Removing ticks on axes and starting (0, 0) at top right.
ax.set_xticks([])
ax.set_yticks([])
ax.invert_yaxis()

def init():
    patch.center = (0, 0)
    for rect in booth_rects:
        ax.add_patch(rect)
    ax.add_patch(patch)
    return [patch] + booth_rects

def animate(i):
    index = i % len(path)
    patch.center = path[index]
    return [patch] + booth_rects

anim = animation.FuncAnimation(fig, animate, 
                               init_func=init,
                               interval=20,
                               blit=True)

plt.show()

