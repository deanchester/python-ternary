import math

import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

"""Matplotlib Ternary plotting utility."""

# # Constants ##

SQRT3OVER2 = math.sqrt(3) / 2.

## Use the default colormap of seaborn
DEFAULT_COLOR_MAP = sns.cubehelix_palette(as_cmap=True)

## Helpers ##
def unzip(l):
    return zip(*l)


def normalize(xs):
    """Normalize input list."""
    s = float(sum(xs))
    return [x / s for x in xs]

## Boundary ##

def draw_boundary(scale=1.0, linewidth=2.0, color='black', ax=None):
    # Plot boundary of 3-simplex.
    if not ax:
        ax = plt.subplot()
    scale = float(scale)
    # Note that the math.sqrt term is such to prevent noticable roundoff on the top corner point.
    ax.plot([0, scale, scale / 2, 0], [0, 0, math.sqrt(scale * scale * 3.) / 2, 0], color, linewidth=linewidth)
    ax.set_ylim((-0.05 * scale, .90 * scale))
    ax.set_xlim((-0.05 * scale, 1.05 * scale))
    return ax


## Curve Plotting ##
def project_point(p):
    """Maps (x,y,z) coordinates to planar-simplex."""
    a = p[0]
    b = p[1]
    c = p[2]
    x = 0.5 * (2 * b + c)
    y = SQRT3OVER2 * c
    return (x, y)


def project(s):
    """Maps (x,y,z) coordinates to planar-simplex."""
    # Is s an appropriate sequence or just a single point?
    try:
        return unzip(map(project_point, s))
    except TypeError:
        return project_point(s)
    except IndexError:  # for numpy arrays
        return project_point(s)


def plot(t, color=None, linewidth=1.0, ax=None):
    """Plots trajectory points where each point satisfies x + y + z = 1.
    First argument is a list or numpy array of tuples of length 3."""
    if not ax:
        ax = plt.subplot()
    xs, ys = project(t)
    if color:
        ax.plot(xs, ys, c=color, linewidth=linewidth)
    else:
        ax.plot(xs, ys, linewidth=linewidth)
    return ax


## Heatmaps##

def simplex_points(steps=100, boundary=True):
    """Systematically iterate through a lattice of points on the 2 dimensional
    simplex."""
    start = 0
    if not boundary:
        start = 1
    for x1 in range(start, steps + (1 - start)):
        for x2 in range(start, steps + (1 - start) - x1):
            x3 = steps - x1 - x2
            yield (x1, x2, x3)


def colormapper(x, a=0, b=1, cmap=None):
    """Maps color values to [0,1] and obtains rgba from the given color map for triangle coloring."""
    if not cmap:
        cmap = DEFAULT_COLOR_MAP
    if b - a == 0:
        rgba = cmap(0)
    else:
        rgba = cmap((x - a) / float(b - a))
    rgba = np.array(rgba)
    rgba = rgba.flatten()
    hex_ = matplotlib.colors.rgb2hex(rgba)
    return hex_


def triangle_coordinates(i, j, alt=False):
    """Returns the ordered coordinates of the triangle vertices for i + j + k = N. Alt refers to the averaged triangles;
    the ordinary triangles are those with base  parallel to the axis on the lower end (rather than the upper end)"""
    # N = i + j + k
    if not alt:
        return [(i / 2. + j, i * SQRT3OVER2), (i / 2. + j + 1, i * SQRT3OVER2),
                (i / 2. + j + 0.5, (i + 1) * SQRT3OVER2)]
    else:
        # Alt refers to the inner triangles not covered by the default case
        return [(i / 2. + j + 1, i * SQRT3OVER2), (i / 2. + j + 1.5, (i + 1) * SQRT3OVER2),
                (i / 2. + j + 0.5, (i + 1) * SQRT3OVER2)]


def i_j_to_x_y(i, j):
    return np.array([i / 2. + j, SQRT3OVER2 * i])

_alpha = np.array([0, 1. / np.sqrt(3)])
_deltaup = np.array([1. / 2., 1. / (2. * np.sqrt(3))])
_deltadown = np.array([1. / 2., - 1. / (2. * np.sqrt(3))])

_i_vec = np.array([1. / 2., np.sqrt(3) / 2.])
_i_vec_down = np.array([1. / 2., -np.sqrt(3) / 2.])

_deltaX_vec = np.array([_deltadown[0], 0])

def hex_coordinates(i, j, steps):
    ij = i_j_to_x_y(i, j)
    coords = np.array([ij + _alpha, ij + _deltaup, ij + _deltadown, ij - _alpha, ij - _deltaup, ij - _deltadown])
    if i == 0:
        # Along the base of the triangle
        if (j != steps) and (j != 0):  # Not a bizarre corner entity
            # Bound at y = zero
            coords = np.array([ij - _deltaX_vec, ij - _deltadown, ij + _alpha, ij + _deltaup, ij + _deltaX_vec])

    if j == 0:
        # Along the left of the triangle
        if (i != steps) and (i != 0):  # Not a corner
            coords = np.array([ij + _i_vec / 2., ij + _deltaup, ij + _deltadown, ij - _alpha, ij - _i_vec / 2.])

    if i + j == steps:
        # Along the right of the triangle
        if (i != 0 ) and (j != 0):
            coords = np.array(
                [ij + _i_vec_down / 2., ij - _alpha, ij - _deltaup, ij - _deltadown, ij - _i_vec_down / 2.])

    # Deal with pathological border cases
    if i == steps and j == 0:
        coords = np.array([ij, ij + _i_vec_down / 2., ij - _alpha, ij - _i_vec / 2.])
    if i == 0 and j == 0:
        coords = np.array([ij, ij + _i_vec / 2., ij + _deltaup, ij + _deltaX_vec])
    if j == steps and i == 0:
        coords = np.array([ij, ij - _deltaX_vec, ij - _deltadown, ij - _i_vec_down / 2.])

    return coords


def heatmap(d, steps, cmap_name=None, boundary=True, ax=None, scientific=False, min_max_scale=None):
    """Plots values in the dictionary d as a heatmap. d is a dictionary of (i,j) --> c pairs where N = steps = i + j + k."""
    if not ax:
        ax = plt.subplot()
    if not cmap_name:
        cmap = DEFAULT_COLOR_MAP
    else:
        cmap = plt.get_cmap(cmap_name)
    if min_max_scale is None:
        a = min(d.values())
        b = max(d.values())
    else:
        a = min_max_scale[0]
        b = min_max_scale[1]
    # Color data triangles.

    for k, v in d.items():
        i, j = k
        vertices = hex_coordinates(i, j, steps)
        if vertices is not None:
            x, y = unzip(vertices)
            color = colormapper(d[i, j], a, b, cmap=cmap)
            ax.fill(x, y, facecolor=color, edgecolor=color)

    # Colorbar hack
    # http://stackoverflow.com/questions/8342549/matplotlib-add-colorbar-to-a-sequence-of-line-plots
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=a, vmax=b))

    # Fake up the array of the scalar mappable. Urgh...
    sm._A = []
    cb = plt.colorbar(sm, ax=ax, format='%.4f')
    cb.locator = matplotlib.ticker.LinearLocator(numticks=7)
    if scientific:
        cb.formatter = matplotlib.ticker.ScalarFormatter()
        cb.formatter.set_powerlimits((0, 0))
    cb.update_ticks()
    return ax


## Convenience Functions ##

def plot_heatmap(func, steps=40, boundary=True, cmap_name=None, ax=None, **kwargs):
    """Computes func on heatmap coordinates and plots heatmap. In other words, computes the function on sample points
    of the simplex (normalized points) and creates a heatmap from the values."""
    d = dict()
    for x1, x2, x3 in simplex_points(steps=steps, boundary=boundary):
        d[(x1, x2)] = func(normalize([x1, x2, x3]))
    heatmap(d, steps, cmap_name=cmap_name, ax=ax, **kwargs)


def plot_multiple(trajectories, linewidth=2.0, ax=None):
    """Plots multiple trajectories and the boundary."""
    if not ax:
        ax = plt.subplot()
    for t in trajectories:
        plot(t, linewidth=linewidth, ax=ax)
    draw_boundary(ax=ax)
    return ax