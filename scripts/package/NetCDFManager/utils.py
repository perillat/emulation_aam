# -*- coding: iso-8859-15 -*-
import os
import numpy as np
import datetime
from functools import reduce

############
## Utils  ##
############


def isAcceptableChar(character):
    return character not in "\x00"

def is_num(str):
    """
    Tests whether a string is a number.

    @type str: string
    @param str: String to be tested.

    @rtype: Boolean
    @return: True if 'str' is a number, False otherwise.
    """
    is_num = True
    try:
        num = float(str)
    except ValueError:
        is_num = False
    return is_num


def is_int(str):
    """
    Tests whether a string is an integer.

    @type str: string
    @param str: String to be tested.

    @rtype: Boolean
    @return: True if 'str' is a integer, False otherwise.
    """
    is_num = True
    try:
        num = int(str)
    except ValueError:
        is_num = False
    return is_num


def to_num(str):
    """
    Converts a string to a number.

    @type str: string
    @param str: String to be converted.

    @rtype: int (preferred) or float
    @return: The number represented by 'str'.
    """
    if is_int(str):
        return int(str)
    elif is_num(str):
        return float(str)
    else:
        raise Exception("\"" + str + "\" is not a number.")


def string_to_datetime(str):
        """
        Converts a string into a datetime object.

        @type str: string
        @param str: String to be converted. It must be in format YYYY, YYYYMM,
        YYYYMMDD, YYYYMMDDHH, YYYYMMDDHHMM or YYYYMMDDHHMMSS. Delimiters (any
        character except numbers) can be added around the month, the day, etc.

        @rtype: datetime
        @return: The datetime object corresponding to 'str'.
        """
        # First filters useless characters.
        str = [x for x in str if is_num(x)]
        str = reduce(lambda x, y: x + y, str)

        year = int(str[0:4])
        if len(str) > 5:
            month = int(str[4:6])
        else:
            month = 1
        if len(str) > 7:
            day = int(str[6:8])
        else:
            day = 1
        if len(str) > 9:
            hour = int(str[8:10])
        else:
            hour = 0
        if len(str) > 11:
            minute = int(str[10:12])
        else:
            minute = 0
        if len(str) > 13:
            sec = int(str[12:14])
        else:
            sec = 0
        return datetime.datetime(year, month, day, hour, minute, sec)


def string_to_datetime_fr(str):
        # First filters useless characters.
        str = [x for x in str if is_num(x)]
        str = reduce(lambda x, y: x + y, str)

        day = int(str[0:2])
        month = int(str[2:4])
        year = int(str[4:8])
        hour = int(str[8:10])
        if len(str) > 11:
            minute = int(str[10:12])
        else:
            minute = 0
        if len(str) > 13:
            sec = int(str[12:14])
        else:
            sec = 0
        return datetime.datetime(year, month, day, hour, minute, sec)


def concat_str(l):
    """
    Cette fonction prend une liste contenant des valeurs (int, float, str) et
    renvoie une chaine de caractères concaténant les éléments de la liste.
    @type l: list
    @param l: liste en entrée
    @rtype: string
    @return: la chaine de caractères concaténée
    """
    return str(reduce(lambda x,y:x+y, [str(li) for li in l]))


def str_to_char(st, Nchar):
    """
    Cette fonction prend en argument une chaine de caractères (string) et renvoie une liste
    de char contenant les caractères de la chaine, et complétée avec des char vides ('')
    pour obtenir la longueur Nchar (ex: Cs-137 avec Nchar=10
    devient ['C', 's', '-', '1', '3', '7', '', '', '', '', ''])
    @param st: chaine de caractères
    @type st: string
    @param Nchar: longueur de la liste renvoyée
    @type Nchar: int
    @return: la liste de caractères
    """
    if Nchar > len(st):
        char_list = np.array([t for t in st] + ['' for i in range(Nchar-len(st))])
    else:
        char_list = np.array([t for t in st])
    return char_list

# Trouver la date la plus proche de date_in dans date_list (pas d'interpolation)
def find_nearest_date_beg(date_in, date_list):
    """
    Recherche de l'indice de date la plus proche de date_in dans la liste date_list
    @param date_in: date recherchée
    @type date_in: date (datetime.datetime)
    @param date_list: liste de dates dans laquelle on cherche date_in
    @type date_in: liste de dates (datetime.datetime)
    @return: indice de la date la plus proche de date_in dans date_list
    (date antérieure ou égale à date_in)
    @rtype: int
    """
    i = 0
    while i < len(date_list)-1 and date_list[i+1] <= date_in :
        i = i+1
    return i


# Trouver la date la plus proche de date_in dans date_list (pas d'interpolation)
def find_nearest_date_end(date_in, date_list):
    """
    Recherche de l'indice de date la plus proche de date_in dans la liste date_list
    @param date_in: date recherchée
    @type date_in: date (datetime.datetime)
    @param date_list: liste de dates dans laquelle on cherche date_in
    @type date_in: liste de dates (datetime.datetime)
    @return: indice de la date la plus proche de date_in dans date_list
    (date postérieure ou égale à date_in)
    @rtype: int
    """
    i = 0
    while i < len(date_list) and date_list[i] < date_in :
        i = i+1
    return i

# Calcule des moyennes temporelles sur un pas de temps spécifié (défaut: moyennes horaires)
def get_average(date_list, value_list, new_dates=[], delta_t=3600., task="mean"):
    # Nouvelles dates toutes les heures piles (si non spécifié)
    if new_dates == []:
        new_dates = []
        for date in date_list:
            minute = date.minute
            date_hour = date - datetime.timedelta(minutes = minute)
            if date_hour not in new_dates:
                new_dates.append(date_hour)

    # Calcul des moyennes temporelles des obs
    mean_values = {}
    for date in new_dates:
        date_min = date  - datetime.timedelta(seconds=delta_t/2.)
        date_max = date + datetime.timedelta(seconds=delta_t/2.)
        mean_values[date] = time_av(date_min, date_max, date_list, value_list, task)
    return mean_values


def time_av(date_beg, date_end, date_list, value_list, task):
    if task == "median":
        return compute_median(date_beg, date_end, date_list, value_list)
    elif task == "mean":
        return compute_mean(date_beg, date_end, date_list, value_list)
    else:
        print("task", task, "unknown.")
        return 0

def compute_median(date_beg, date_end, date_list, value_list):
    tmp = []
    for date, value in zip(date_list, value_list):
        if date >= date_beg and date < date_end:
            tmp.append(value)
    if tmp != []:
        return median(tmp)
    else:
        return 0


def compute_mean(date_beg, date_end, date_list, value_list):
    tmp = []
    for date, value in zip(date_list, value_list):
        if date >= date_beg and date < date_end:
            tmp.append(value)
    if tmp != []:
        return mean(tmp)
    else:
        return 0


# Retourne le nombre de pas de temps et la liste des dates
def get_dates(date_beg, date_end, delta_t):
    """
    Retourne une liste de dates, comprise entre date_beg et date_end, avec un pas de temps delta_t
    @param date_beg: date de début
    @type date_beg: date (datetime.datetime)
    @param date_end: date de fin
    @type date_end: date (datetime.datetime)
    @param delta_t: pas de temps en secondes
    @type delta_t: float
    @return:  nombre de dates et liste de dates
    @rtype:  int, list
    """
    Nt = (date_end - date_beg).days * 24 * 3600 + (date_end - date_beg).seconds
    Nt = int(Nt / delta_t) + 1
    date_list = [date_beg + datetime.timedelta(seconds=i*delta_t) for i in range(Nt)]
    return date_list

# Transforme une date (str) en datetime et la passe en JST si nécessaire
def get_date_JST(date_str, format):
    date = string_to_datetime(date_str)
    if "UT" in format:
        date = date + datetime.timedelta(hours=9)
    return date


# Transforme une date (str) en datetime et la passe en UT si nécessaire
def get_date_UT(date_str, format):
    date = string_to_datetime(date_str)
    if "JST" in format:
        date = date - datetime.timedelta(hours=9)
    return date

# Retourne la date à l'heure pile (enlève les minutes et les secondes)
def get_date_hour(date):
    date_hour = date - datetime.timedelta(minutes=date.minute)
    date_hour = date_hour - datetime.timedelta(seconds=date.second)
    return date_hour

def truncateDates(date_beg, date_end, dates):
    """
    Indices de début et de fin pour tronquer la liste dates aux dates données
    @param date_beg: indice ou date de début
    @type date_beg: int ou datetime
    @param date_end: indice ou date de fin
    @type date_end: int ou datetime
    @param dates: liste de dates à tronquer
    @type dates: list
    """
    if type(date_beg) == int and type(date_end) == int:
        ind_beg = date_beg
        if date_end > len(dates) or date_end == -1:
            date_end = len(dates) - 1
        ind_end = date_end
    else:
        if date_beg > dates[-1] or date_end < dates[0]:
            print("Les dates de debut et de fin ne sont pas comprises dans la plage de rejet")
            return -999, -999
        else:
            # Recherche des indices de début et de fin
            ind_beg = find_nearest_date_beg(date_beg, dates)
            ind_end = find_nearest_date_end(date_end, dates)
    return ind_beg, ind_end

def increment(variable, value):
    if variable[-1].isdigit():
        variable = variable[0:-1] + str(value)
    return variable

def find_cell(value, l, delta):
    ind=0
    while ind < len(l) and l[ind]+delta < value:
        ind += 1
    return ind

# Interpolation linéaire de base
def interpolate(z, z1, z2, w1, w2):
    if z2 > z1 and z >= z2:
        return w2
    elif z2 > z1 and z <= z1:
        return w1
    elif z1 > z2 and z <= z2:
        return w2
    elif z1 > z2 and z >= z1:
        return w1
    else:
        w = w1 + (z - z1) * (w2 - w1) / (z2 - z1)
        return w



# Points sur un cercle
def get_circle(r, Nangle=100):
    xlist = []
    ylist = []
    # print("circle of distance", r)
    for i in range(1, Nangle+1):
        x = r*cos(2*i*pi/float(Nangle))
        y = r*sin(2*i*pi/float(Nangle))
        # print(i, x, y)
        xlist.append(x)
        ylist.append(y)
    return xlist, ylist

# Création de maillages 3D à partir de listes
def create_3D_grid(x_list, y_list, z_list):
    x2D, y2D = np.meshgrid(x_list, y_list)
    (Ny, Nx) = x2D.shape

    Nz = len(z_list)
    x = np.zeros((Nz, Ny, Nx), 'd')
    y = np.zeros((Nz, Ny, Nx), 'd')
    z = np.zeros((Nz, Ny, Nx), 'd')

    for i in range(Nz):
        x[i] = x2D
        y[i] = y2D
        z[i].fill(z_list[i])
    return x, y, z
