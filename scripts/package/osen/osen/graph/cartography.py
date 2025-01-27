# -*- coding: utf-8 -*-
# Author: Sylvain Girard (girard@phimeca.com)
"""Draw maps.
"""
# TODO: imported from OLD_Ubik on 21-7-21. Probably needs cleanup.
# TODO: clean docstrings.

#§
import numpy as np
from matplotlib import pyplot as plt
import matplotlib.pyplot
from matplotlib import colors

#§
def exceedance(data, threshold, dtype=float):
    """Threshold a map.

    Args:
        data (list of array): data sample.
        threshold (float).
        dtype (dtype): data type, default is float.

    Returns:
        out (array): binary map of exceedance (1.) and non exceedance (0.).

    """

    out = np.greater(data, threshold).astype(dtype)
    return out

def compute_error_exceedance(prediction, target, threshold):
    """Compute error of exceedance prediction.

    Args:
        prediction (array).
        target (array):.
        threshold: float.

    """
    error = (1.*exceedance(prediction, threshold) -
             1.*exceedance(target, threshold))
    #TODO: dtype is not used in cartography.exceedance
    return error

def exceedance_probability(data, threshold):
    """Compute the empirical probability of exceedance of a threshold.

    Args:
        data: Sequence of array, data sample.
        threshold (float):.
    """

    probability = exceedance(data, threshold).mean(0)
    return probability

def difference_exceedance_probability(pair_data, threshold):
    """Compute the empirical probability of exceedance of a threshold.

    Args:
        pair_data: Pair of sequences of array, data sample.
        threshold (float):.

    """

    data_a, data_b = pair_data
    probability_a = exceedance_probability(data_a, threshold)
    probability_b = exceedance_probability(data_b, threshold)
    return probability_a - probability_b

#§ Graphics
def step_spatial_to_n_cell(coordinate, step_spatial, lower_left=None):
    """Convert coordinates in spatial unit to numbers of cells.

    Args:
        coordinate: Sequence of floats, coordinates in spatial unit.
        step_spatial (float): spatial step.
        lower_left: Sequence of floats, coordinates of lower left corner of the
            frame.

    """

    if lower_left is None:
        lower_left = np.zeros_like(coordinate)

    translated = np.subtract(coordinate, lower_left)
    n_cell = translated / float(step_spatial)

    return n_cell


def draw_map(data, color_map=None, list_color=None, transformation=None,
             ax=None, step_spatial=1., coordinate_source=None,
             mesh=None,
             symmetric_span=False, drawer=None,
             kwargs_imshow=None, **kwargs):
    """Draw a map of possibly transformed data.

    Args:
        data (2d array): simulated data. Alternaltively, input of
            'transformation'.
        color_map: Matplotlib color map.
        list_color: Sequence of color identifiers, overwrite color map by a
            discrete list of colors.
            # If a single (non iterable) color is passed, prepend "none". TODO: does not work in py3
        transformation: Function, output a 2d array from 'data'.
        ax: Matplotlib axis.
        step_spatial (float): spatial step size.
        coordinate_source: Pair of floats, coordinate of the source (in number
            of spatial cells).
        mesh: spary.MeshRegular2D instance.
        symmetric_span (bool): if True, make the color mapped interval
            symmetric around 0. Default is False.
        drawer (str): select function used for drawing the map. one of
            "imshow" (default), or "hs_imshow".
        kwargs_imshow: Dictionary, keyword arguments passed on to plt.imshow.
        **kwargs: passed on to 'transformation'.
    """

    if color_map is None:
        color_map = matplotlib.pyplot.cm.Greys

    if list_color is not None:
        # try:
        #     list_color.__iter__
        # except AttributeError:
        #     list_color = [list_color]

        if len(list_color) == 1:
            list_color.insert(0, "none")

        color_map = colors.ListedColormap(list_color)


    if drawer is None:
        drawer = "imshow"

    if ax is None:
        ax = plt.gca()

    if transformation is None:
        transformation = lambda z: z

    transformed = transformation(data, **kwargs)
    # TODO: other data could be retrieve from mesh
    if mesh is not None:
        transformed = transformed.reshape(mesh.shape)

    n_x, n_y = transformed.shape
    # left, right, bottom, top
    if coordinate_source is None:
        extent = (0, n_x * step_spatial, 0, n_y * step_spatial)
    else:
        coordinate_source_step = np.array(coordinate_source) * step_spatial
        extent = (0 - coordinate_source_step[0],
                  n_x * step_spatial - coordinate_source_step[0],
                  0 - coordinate_source_step[1],
                  n_y * step_spatial - coordinate_source_step[1])

    if kwargs_imshow is None:
        kwargs_imshow = dict()
    else:
        # To avoid altering a passed dictionary.
        kwargs_imshow = kwargs_imshow.copy()

    kwargs_imshow.setdefault("interpolation", "none")
    kwargs_imshow.setdefault("origin", "lower")
    kwargs_imshow.setdefault("cmap", color_map)
    kwargs_imshow.setdefault("extent", extent)

    if drawer == "imshow":
        image = ax.imshow(transformed, **kwargs_imshow)
    elif drawer == "hs_imshow":
        import hillshade.graphics
        image = hillshade.graphics.imshow_hs(transformed, ax=ax,
                                             **kwargs_imshow)


    if symmetric_span:
        absolute_maximum = np.max(np.abs(transformed))
        symmetric_span = (-absolute_maximum, absolute_maximum)
        image.set_clim(symmetric_span)

    # if coordinate_source is not None:
    #     ax.plot(0, 0, marker="o", ms=6, mew=2, color="coral",
    #             mec="black",
    #             scalex=False, scaley=False)

    return image, transformed

#§
def plot_source(ax, coordinate_source=None, **kwargs):
    """Add a dot marking source (or other point of interest).

    Args:
        ax: Matplotlib axis.
        coordinate_source: Pair of floats, coordinate of the source (in number
            of cells).


    """
    if coordinate_source is None:
       coordinate_source = (0, 0)

    kwargs.setdefault("marker", "o")
    kwargs.setdefault("ms", 6)
    kwargs.setdefault("mew", 2)
    kwargs.setdefault("color", "coral")
    kwargs.setdefault("mec", "black")
    kwargs.setdefault("scalex", False)
    kwargs.setdefault("scaley", False)
    kwargs.setdefault("label", "Source")
    kwargs.setdefault("linestyle", "none")
    plot = ax.plot(coordinate_source[0],
                   coordinate_source[1], **kwargs)
    return plot

#§
# TODO: make it more generic.
def draw_map_error_exceedance(target, prediction, ax, threshold,
                              # transformation=None, # TODO: Disabled for now.
                              color_exceedance="darkseagreen",
                              color_false_positive="orange",
                              color_non_detection="purple",
                              **kwargs):
    """TODO"""
    # interpolation = "bicubic" -> kwargs_imshow

    error = compute_error_exceedance(prediction=prediction, target=target,
                                     threshold=threshold)

    transformation_target = lambda zz: exceedance(zz, threshold=threshold)

    transformation_error = lambda zz: exceedance(zz, threshold=.5)

    draw_map(data=target, ax=ax,
             list_color=[color_exceedance],
             transformation=transformation_target,
             **kwargs)


    draw_map(data=-error, ax=ax,
             list_color=[color_non_detection],
             transformation=transformation_error,
             **kwargs)

    draw_map(data=error, ax=ax,
             list_color=[color_false_positive],
             transformation=transformation_error,
             **kwargs)

    # plot_source(ax=ax)
    # ax.set_xlim(xy_lim)
    # ax.set_ylim(xy_lim)

#§ For contours
from scipy.interpolate import RectBivariateSpline

def smooth(data, factor_smoothing=None):
    """Smooth a surface using spline interpolation

    Args:
        data (array).
        factor_smoothing (float): divide the number of grid steps by this
            amount.
    """

    if factor_smoothing is None:
        data_smooth = data
        return data_smooth

    n_x, n_y = data.shape
    smoother = RectBivariateSpline(np.linspace(0, 1, n_x),
                                   np.linspace(0, 1, n_y), data,
                                   kx=3, ky=3, s=0)
    data_smooth = smoother(np.linspace(0, 1, int(n_x/ factor_smoothing)),
                           np.linspace(0, 1, int(n_x/ factor_smoothing)))

    return data_smooth

def draw_contour(data, extent, level=None, n_level=None, color=None,
                 factor_smoothing=None, ax=None, flag_label=True,
                 fill=False, **kwargs):
    """Draw contours.

    Args:
        data (array):.
        extent: See matplotlib.pyplot.imshow:extent.
        level: Sequence of floats, levels.
        n_level (int): number of automatically chosen levels if level is not
            provided.
        color: See matplotlib.pyplot.contour:colors.
        factor_smoothing: Optional float, divide the number of grid steps by
            this amount.
        ax: Matplotlib axis.
        flag_label (bool): toggle adding labels. Default is True.
        **kwargs: passed on to 'patplotlib.pyplot.contour'.
    """


    if ax is None:
        ax = plt.gca()

    if factor_smoothing is not None:
        data_smooth = smooth(data, factor_smoothing)
    else:
        data_smooth = data

    try:
        image = extent
        extent = image.get_extent()
    except AttributeError:
        pass

    if fill:
        drawer = ax.contourf
    else:
        drawer = ax.contour

    contour = drawer(data_smooth,
                     n_level,
                     extent=extent,
                     # scalex=False, scaley=False, # TODO: Obsolete?
                     antialiased=False,
                     linewidths=1.,
                     levels=level, colors=color, **kwargs)
    if flag_label:
        plt.clabel(contour, fontsize=10, inline_spacing=8, fmt="%g")
    return contour

#§
