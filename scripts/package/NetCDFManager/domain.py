#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from . import nc
import numpy as np
import datetime
try:
    from . import convert_coords
except:
    print("Impossible d'importer convert_coords: attention, ne pas tenter de convertir des lat/lon en cartesien")
    pass



#################
# CLASSE DOMAIN #
#################


class Domain(nc.NC):
    """
    Manipulation fichiers de maillages et résultats demandés (fichier nc).
    La classe Domain dérive de la classe générique NC.
    """
    def __init__(self, fileName=""):
        """
        Initialise la classe Domain.
        Récuperation des caracteristiques du maillage.

        """
        # Initialisation globale
        nc.NC.__init__(self, fileName, 'd')


    ##########################
    # MANIPULATION DES DATES #
    ##########################


    def getDateList(self, index=0):
        """
        Calcule la liste de dates auxquelles les résultats sont demandés
        @param index: Indice du résultat demandé. Défaut: 0
        @type index: int
        @return: la liste de dates
        @rtype: list
        """
        time_list = self.variables['ResultTime' + str(index)]
        date_ref = string_to_datetime_fr(self.variables['TimeRef'])
        date_list = [date_ref + datetime.timedelta(seconds = float(t)) for t in time_list]
        return date_list


    def setTimeList(self, time_list, index=0):
        """
        Modification de la liste d'instants demandés (sans modification du TimeRef)
        @param time_list: Liste des nouveaux instants demandés
        @type time_list: float list
        @param index: Indice du résultat demandé. Défaut: 0
        @type index: int
        """
        varkey = 'ResultTime'+str(index)
        dimkey = 'NTimeResult'+str(index)

        # Dimension
        self.dimensions[dimkey] = len(time_list)

        # Si les variables n'existent pas encore, tout est rajouté aux dictionnaires
        if varkey not in self.variables.keys():
            attr = {"long_name": "Instants de resultats demandes",
                    "units": "s"}
            self.createVariable(varkey, np.array(time_list, dtype='d'), (dimkey,), attr, 'd')
        else:
            self.variables[varkey] = np.array(time_list, dtype='d')



    #######################################
    # MODIFICATION DES RÉSULTATS DEMANDÉS #
    #######################################


    def getResultType(self, index=0):
        return self.globalAttr["Result_Type" + str(index)]


    def setResultType(self, result_type, index=0):
        """
        Modifie le type de résultats demandés
        @param result_type: 1 pour Inst, 2 pour Integ, 3 pour Dep et 4 pour tout
        @type result_type: int
        """
        self.globalAttr["Result_Type" + str(index)] = str(result_type)


    def addResult(self, date_list, result_type, point_index = 0, result_name = ""):
        """
        Ajoute un résultat demandé
        @param date_list: Liste des dates demandées
        @type date_list: datetime list
        @param result_type: 1 pour Inst, 2 pour Integ, 3 pour Dep et 4 pour tout
        @type result_type: int
        @param point_index: indice du maillage associé (défaut: 0)
        @type point_index: int
        @param result_name: nom du nouveau résultat (défaut: "Resultat x" avec x = indice + 1)
        @type result_name: string
        """
        # Indice du nouveau résultat
        if "NResult" not in self.variables.keys():
            attr = {'long_name': 'Nombre de resultat',
                    'units': ''}
            self.createVariable("NResult", 1, (), attr, 'i')
            index = 0
        else:
            Nr = int(self.variables["NResult"])
            index = Nr
            self.variables["NResult"] = Nr + 1

        # Nom du résultat demandé
        self.globalAttr['Result_long_name' + str(index)] = "Resultat " + str(index + 1)

        # Instants demandés
        self.setDateList(date_list, index)

        # Type de résultats demandés
        self.setResultType(result_type)

        # Maillage associé
        self.globalAttr["Result_RefPointsSet" + str(index)] = str(point_index)


########################################
# FONCTIONS DE CRÉATION DE FICHIERS NC #
########################################


def createDomain(file_out, x, y, z, date_beg, date_end, delta_t = 3600., result_type=4, name_list = []):
    """
    file_out: nom du fichier (nc) de sortie
    x, y, z: coordonnées du maillage au bon format
    date_beg: début des résultats demandés
    date_end: fin des résultats demandés
    delta_t: pas de temps des résultats demandés, en secondes (défaut: 3600 s)
    name_list: liste des noms de balises: uniquement si liste de points (défaut: [])
    result_type: 1 pour Inst, 2 pour Integ, 3 pour Dep et 4 pour tout (défaut: 4)
    """
    # Création d'une instance de la classe Domain à vide
    d = Domain()
    point_index = d.createPointSet(x, y, z, name_list)

    # Temps demandés
    d.setTimeRef(date_beg)
    Nt = (date_end - date_beg).days * 24 * 3600 + (date_end - date_beg).seconds
    Nt = int(float(Nt) / delta_t) + 1
    date_list = [date_beg + datetime.timedelta(seconds=t*delta_t) for t in range(Nt)]

    # Ecriture du fichier de résultats demandés
    d.addResult(date_list, result_type, point_index)
    d.writeNC(file_out)


## Écriture d'un fichier contenant un maillage circulaire
def createPolarMesh(file_out, rlist, delta_angle, angle_min, angle_max, \
                        date_beg, date_end, delta_t = 3600., result_type = 4, zlist = []):
    """
    file_out: nom du fichier (nc) de sortie
    rlist: liste des rayons
    delta_angle: pas (en degrés, ou même unité que angle_max)
    angle_min: premier angle, en degrés (pour savoir où commence le cercle)
    angle_max: ouverture du domaine
    date_beg: début des résultats demandés
    date_end: fin des résultats demandés
    delta_t: pas de temps des résultats demandés, en secondes (défaut: 3600 s)
    result_type: 1 pour Inst, 2 pour Integ, 3 pour Dep et 4 pour tout (défaut: 4)
    """

    # Création du maillage
    Nr = len(rlist)
    Nangle = int((angle_max-angle_min) / delta_angle)
    Nz = max(1, len(zlist))
    print("Nombre de niveaux verticaux:", Nz)
    print("Nombre de rayons:", Nr)
    print("Nombre de points sur chaque rayon", Nangle+1)

    x = zeros((Nz, Nangle+1, Nr),'d')
    y = zeros((Nz, Nangle+1, Nr),'d')
    z = zeros((Nz, Nangle+1, Nr),'d')
    for i, r in enumerate(rlist):
        xmin = r*cos(2*pi*angle_min / 360.)
        ymin = r*sin(2*pi*angle_min / 360.)
        alpha_list = [angle_min + j*delta_angle for j in range(Nangle+1)]
        xlist = np.array([r*cos(2*pi*alpha / 360.) for alpha in alpha_list])
        ylist = np.array([r*sin(2*pi*alpha / 360.) for alpha in alpha_list])
        for j in range(Nangle+1):
            for k in range(Nz):
                x[k,j,i] = xlist[j]
                y[k,j,i] = ylist[j]
                if zlist != []:
                    z[k,j,i] = zlist[k]
                else:
                    z[k,j,i] = 0.


    createDomain(file_out, x, y, z, date_beg, date_end, delta_t, result_type)
    return x, y, z


## Écriture d'un fichier contenant un maillage cartésien
def createCartesianMesh(file_out, x_list, y_list, date_beg, date_end, delta_t = 3600., result_type = "4"):
    """
    file_out: nom du fichier (nc) de sortie
    x_list: liste des abscisses
    y_list: liste des ordonnées
    date_beg: début des résultats demandés
    date_end: fin des résultats demandés
    delta_t: pas de temps des résultats demandés, en secondes (défaut: 3600 s)
    result_type: 1 pour Inst, 2 pour Integ, 3 pour Dep et 4 pour tout (défaut: 4)
    """
    # Liste des distances
    Nx = len(x_list)
    Ny = len(y_list)
    x, y = meshgrid(x_list, y_list)
    z = zeros((1, Ny, Nx),'d')
    x= x.reshape(1, Ny, Nx)
    y= y.reshape(1, Ny, Nx)
    x = double(x)
    y = double(y)
    createDomain(file_out, x, y, z, date_beg, date_end, delta_t, result_type)
    return x, y


## Ecriture des resultats demandés à partir d'une liste de points en lat/lon
def createPointList(file_in, file_out, date_beg, date_end, delta_t = 3600., result_type = 4,
                    latlon=False, xref=0, yref=0, zone='54'):
    """
    file_in: nom du fichier contenant la liste des balises avec les coordonnées (3 colonnes: nom/x/y)
    file_out: nom du fichier nc de résultats demandés qui sera créé
    date_beg: date de début des résultats demandés (datetime)
    date_end: date de fin des résultats demandés (datetime)
    delta_t: pas de temps des résultats demandés, en secondes (défaut: 3600 s)
    latlon: si True, ce sont des coordonnées en latitude/longitude qui sont données, et la conversion en cartésien est faite (défaut: False)
    xref: longitude de la source pour la conversion en cartésien
    yref: latitude de la source pour la conversion en cartésien
    zone: zone UTM pour la conversion (54 pour le Japon, 30, 31 ou 32 pour la France) (en str)
    """
    # Lecture du fichier de balises
    f = open(file_in, 'r')
    name_list = []
    x_list = []
    y_list = []
    for line in f.xreadlines():
        l = line.split()
        if len(l) != 0 and l[0] != "#":
            name_list.append(l[0])
            x_list.append(float(l[1]))
            y_list.append(float(l[2]))
    f.close()
    if latlon:
        x_list, y_list = convert_coords.convert_latlon_to_cartesian(np.array(x_list), np.array(y_list), xref, yref, zone)
        for i in range(len(name_list)):
            print(name_list[i], x_list[i], y_list[i], sqrt(x_list[i]*x_list[i]+y_list[i]*y_list[i])/1000.)

    x = np.array(x_list, dtype = 'd')
    y = np.array(y_list, dtype = 'd')
    z = zeros(x.shape, dtype = 'd')
    createDomain(file_out, x, y, z, date_beg, date_end, delta_t, result_type, name_list)

    return x_list, y_list


## Ecriture des resultats demandés à partir d'une liste de points en r/theta
def createPointListRtheta(file_in, file_out, date_beg, date_end, delta_t = 3600., result_type = 4):
    """
    file_in: nom du fichier contenant la liste des balises avec les coordonnées (3 colonnes: nom/r/theta), avec theta l'angle trigo
    file_out: nom du fichier nc de résultats demandés qui sera créé
    date_beg: date de début des résultats demandés (datetime)
    date_end: date de fin des résultats demandés (datetime)
    delta_t: pas de temps des résultats demandés, en secondes (défaut: 3600 s)
    """
    # Lecture du fichier de balises
    f = open(file_in, 'r')
    rlist = []
    theta_list = []
    name_list = []
    for line in f.xreadlines():
        l = line.split()
        if len(l) != 0 and l[0] != "#":
            name_list.append(l[0])
            rlist.append(float(l[1]))
            theta_list.append(float(l[2])) # Angle trigo
    f.close()
    Np = len(name_list)
    xlist = [rlist[i] * cos(radians(theta_list[i])) for i in range(Np)]
    ylist = [rlist[i] * sin(radians(theta_list[i])) for i in range(Np)]

    x = np.array(xlist, dtype = 'd')
    y = np.array(ylist, dtype = 'd')
    z = zeros(x.shape, dtype = 'd')
    createDomain(file_out, x, y, z, date_beg, date_end, delta_t, result_type, name_list)

    return xlist, ylist
