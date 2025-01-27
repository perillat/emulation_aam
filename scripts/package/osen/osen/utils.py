import os
import numpy as np
from matplotlib.collections import PolyCollection

def makedir(path):
    if os.path.exists(path) == False:
        os.makedirs(path)


def interpolation(x1, x2, y1, y2, y):
    """
    Find the x value corresponding to y by interpolating between the points (x1, y1) and (x2, y2).
    """
    a = (y2 - y1)/(x2 - x1)
    b = y2 - a*x2
    x = (y - b)/a
    return x


def affected_angles(direction, opening_angle):
    """
    Renvoie une liste d'angles (en degrés) inclus dans la portion de cercle.

    Paramètres :
    - direction: L'angle de direction, centre de la portion de cercle.
    - opening_angle: L'ouverture angulaire.

    Renvoie:
    - Une liste d'angles (en degrés).
    """

    # Calcul des angles limites
    start_angle = direction - (opening_angle / 2)
    end_angle = direction + (opening_angle / 2)

    # Corrigez les angles pour qu'ils soient dans [0, 360)
    start_angle = start_angle % 360
    end_angle = end_angle % 360

    # Générer la liste des angles
    if start_angle < end_angle:
        angles = list(range(int(start_angle), int(end_angle)))
    else:
        # Cas où la portion traverse la ligne 0/360°
        angles = list(range(int(start_angle), 360)) + list(range(0, int(end_angle)))

    return angles

def count_angles(all_angle_lists):
    """
    Compte les occurrences de chaque angle et renvoie les pourcentages.

    Paramètres :
    - all_angle_lists: Une liste de listes, chaque sous-liste contenant les angles inclus pour une direction/ouverture donnée.

    Renvoie:
    - Un tableau (array) où l'index est l'angle et la valeur est le pourcentage d'occurrences.
    """
    angle_counts = np.zeros(360)  # Initialisez un tableau de taille 360 avec des zéros

    # Parcourez chaque liste d'angles et mettez à jour le tableau
    for angle_list in all_angle_lists:
        for angle in angle_list:
            angle_counts[angle] += 1

    # Normalisez pour obtenir les pourcentages
    total_angles = len(all_angle_lists)
    if total_angles != 0:  # Évitez une division par zéro
        angle_counts = (angle_counts / total_angles) * 100

    return angle_counts

def draw_bar_contour(ax, x, y, color, edgecolor, alpha=1.0):
    # Ajoutez un zéro au début et à la fin des y pour descendre au niveau de l'axe des x
    y_ext = np.concatenate(([0], y, [0]))
    x_ext = np.concatenate(([x[0]], x, [x[-1]+1]))

    # Utilisez fill_between pour remplir la zone, ce qui donne l'effet de barres
    ax.fill_between(x_ext, y_ext, color=color, alpha=alpha, step='post')

    # Dessinez le contour de l'ensemble des barres
    ax.plot(x_ext, y_ext, color=edgecolor, alpha=alpha)


# Fonction pour ajouter un contour autour d'une série de données
def add_contour(x, data, color='black'):
    bottom_points = list(zip(x, np.zeros_like(x)))
    top_points = list(zip(x, data))
    bottom_points = bottom_points[::-1]
    contour_points = top_points + bottom_points
    poly = PolyCollection([contour_points], edgecolor=color, facecolor="none")
    return poly
