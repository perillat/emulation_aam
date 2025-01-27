#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from . import nc
from . import utils
import datetime

try:
    from gisx import giveConvAngle
except:
    print("import du module gisx impossible")

import math
import numpy as np

#########################
# FONCTIONS SUR LE VENT #
#########################


# Conversion de la direction du vent dans un repère trigonométrique.
def windProjection(wind, direction, xRef=None, yRef=None, proj=None):
    """
    Renvoie le vecteur vent à partir de la vitesse et la direction du vent.
    @type vitesse: float
    @param vitesse: vitesse du vent.
    @type direction: float
    @param direction: direction du vent exprimée en degrés météo (0 = vent du nord).
    @param xRef: longitude du point de reference (pour calculer la convergence des méridiens)
    @type xRef: float
    @param yRef: latitude du point de reference (pour calculer la convergence des méridiens)
    @type yRef: float
    @type projection: string soit "L93" soit "L2E", soit "WGS84" etc.
    @param projection:  Système des coordonnées.
    @rtype: tuple
    @return: les projections du vent sur les axes x et y.
    """
    # Prise en compte de la déclinaison des meridiens.
    if None not in (xRef, yRef, proj):
        devAng = giveConvAngle(xRef, yRef, proj)
        direction += devAng

    # Conversion en angle trigonométrique.
    angle = - math.pi / 2. - direction * math.pi / 180.
    cosAngle = math.cos(angle)
    if math.fabs(cosAngle) < 1.e-8:
        cosAngle = 0.
    sinAngle = math.sin(angle)
    if math.fabs(sinAngle) < 1.e-8:
        sinAngle = 0.

    return wind * cosAngle, wind * sinAngle


def computeWindDir(U,V, xRef=None, yRef=None, proj=None):
    """
    Calcul de la vitesse et la direction du vent à partir des composantes U et V
    @para U: vent zonal (m/s)
    @type U: float
    @param V: vent meridional (m/s)
    @type V: float
    @param xRef: longitude du point de reference (pour calculer la convergence des méridiens)
    @type xRef: float
    @param yRef: latitude du point de reference (pour calculer la convergence des méridiens)
    @type yRef: float
    @type projection: string soit "L93" soit "L2E", soit "WGS84" etc.
    @param projection:  Système des coordonnées.
    @rtype: tuple
    @return: vitesse (m/s) et direction du vent exprimée en degrés météo (0 = vent du nord).
    """
    ff = sqrt(U*U + V*V)

    if U >= 0 and V > 0:
        dd2 = degrees(atan(U/V)) + 180.
        dd3 = degrees(abs(acos(float(V)/ff))) + 180.
    elif U >= 0. and V < 0.:
        dd2 = degrees(atan(U/V)) + 360.
        dd3 = 360. - degrees(abs(acos(abs(float(V))/ff)))#abs(degrees(atan(U/V)))
    elif U < 0. and V > 0.:
        dd2 = degrees(atan(U/V)) + 180.
        dd3 = 180. - degrees(acos(float(V)/ff))#abs(degrees(atan2(U,V)))
    elif U < 0. and V < 0.:
        dd2 = degrees(atan(U/V))
        dd3 = degrees(acos((float(-V))/ff))
    elif abs(V) == 0.:
        dd2 = abs(degrees(atan2(U,V)))
        dd3 = (degrees(acos(float(V)/ff)))

    # Prise en compte de la déclinaison des meridiens.
    if None not in (xRef, yRef, proj):
        devAng = giveConvAngle(xRef, yRef, proj)
        dd3 -= devAng

    return ff, dd3

def convertWind(wind, direction, xRef=None, yRef=None, proj=None):
    """
    Applique windProjection à des listes de vitesses et directions de vent
    """
    u_list = []
    v_list = []
    for speed, angle in zip(wind, direction):
        u, v = windProjection(speed, angle, xRef, yRef, proj)
        u_list.append(u)
        v_list.append(v)
    return u_list, v_list



#################
# CLASSE METEO #
#################


class Meteo(nc.NC):
    """
    Manipulation fichiers météo pour px (fichier nc).
    La classe Meteo dérive de la classe générique NC.
    """
    def __init__(self, fileName=""):
        """
        Initialise la classe Meteo.
        """
        # Initialisation globale
        nc.NC.__init__(self, fileName, 'd')

        # Attributs des variables, même si elles n'existent pas encore (ce sont toujours les mêmes noms...)
        if fileName == "":
            self.variableAttr = {"VitU": {"long_name": "Vit U ", "units": "m/s"},
                                 "VitV": {"long_name": "Vit V", "units": "m/s"},
                                 "VitW": {"long_name": "Vit W", "units": "m/s"},
                                 "SigV":{"long_name": "Ecart type du vent suivant y", "units": "m/s"},
                                 "SigW":{"long_name": "Ecart type du vent suivant z", "units": "m/s"},
                                 "TLY":{"long_name": "Echelle de temps lagrangienne suivant y", "units": "s"},
                                 "TLZ":{"long_name": "Echelle de temps lagrangienne suivant z", "units": "s"},
                                 "Stab": {"long_name": "Stability", "units": ""},
                                 "Rain": {"long_name": "Rain", "units": "mm/h"},
                                 "HCLA": {"long_name": "Hauteur de la CLA", "units": "m"},
                                 "Ustar": {"long_name": "Vitesse de friction", "units": "m/s"},
                                 "LMO": {"long_name": "Longueur de Monin-Obukhov", "units": "m"}}
            self.globalAttr["Meteo_long_name"] = "météo"

        # Pour savoir quels champs sont 2D ou 3D
        self.variable3D = ["VitU", "VitV", "VitW", "SigV", "SigW", "TLY", "TLZ"]
        self.variable2D = ["Stab", "Rain", "HCLA", "Ustar", "LMO"]


    def computeWind(self, xRef=None, yRef=None, proj=None):
        """
        Calcule et retourne la vitesse et direction du vent, connaissant U et V
        """
        self.wind=np.zeros(self.variables["VitU"].shape)
        self.direction=np.zeros(self.variables["VitU"].shape)

        for t in range(self.wind.shape[0]):
            for z in range(self.wind.shape[1]):
                for y in range(self.wind.shape[2]):
                    for x in range(self.wind.shape[3]):
                        u = self.variables["VitU"][t,z,y,x]
                        v = self.variables["VitV"][t,z,y,x]
                        self.wind[t,z,y,x], self.direction[t,z,y,x] = computeWindDir(u, v)


    ########################################
    # INITIALISATION AVEC UN FICHIER TEXTE #
    ########################################


    def loadTxt(self, filename, x_width=100000, y_width=100000, z_list=[0,2000], delimiter="\t"):
        """
        Chargement des paramètres météo à partir d'un fichier texte
        La première ligne doit contenir des labels (noms de variables météo) -- éviter les accents
        Les lignes commentées sont ignorées
        Les autres lignes doivent contenir les dates puis valeurs des variables, séparées par des tabulations
        Les valeurs uniformes sont mises sur un maillage spécifié dans les arguments de la fonction
        """

        # Création maillage 1D
        self.createPointSet1D(x_width, y_width, z_list)

        # Lecture fichier texte
        meteo = loadtxt(filename, delimiter = delimiter, unpack=True, dtype='S')
        labels = meteo[:, 0]
        labels = [l.strip() for l in labels]

        # Boucle sur les lignes (hors entête): récupération des dates
        date_list = []
        met_dic = {}
        for i in range(1, meteo.shape[1]):
            try:
                date_list.append(utils.string_to_datetime_fr(meteo[0, i] +"_" + meteo[1, i]))
            except ValueError:
                date_list.append(utils.string_to_datetime(meteo[0, i] +"_" + meteo[1, i]))

            # Autres variables météo
            for j, label in enumerate(labels[2:]):
                try:
                    value = float(meteo[j+2, i])
                except ValueError:
                    if meteo[j+2, i] == "DN":
                        value = 2
                    elif meteo[j+2, i] == "DF":
                        value = 4
                    else:
                        print("Valeur non acceptable pour la variable", label, ":", meteo[j+2, i])

                if value not in [-9999, -999, -99]:
                    try:
                        met_dic[label].append(value)
                    except KeyError:
                        met_dic[label] = [value]
                else:
                    print("Valeur non acceptable pour la variable", label, ":", value)

        # Création liste d'instants
        self.setDateList(date_list, True)

        # Valeurs par défaut
        field_dic = {"VitU": 2.,
                     "VitV": 0.,
                     "VitW": 0.,
                     "Stab": 3,
                     "Rain": 0.,
                     "HCLA": 1000.}

        # Correspondance entre les labels et les variables de l'instance météo
        wind_list = []
        angle_list = []
        u_list = []
        v_list = []
        for label in met_dic.keys():
            name = label
            if label.lower() in ["stabilite", "stability", "stab"]:
                name = "Stab"
            elif label.lower() in ["p", "p0", "precipitation", "pluie", "rain"]:
                name = "Rain"
            elif label.lower() in ["h", "hcla", "blh", "hcl", "boundary_height"]:
                name = "HCLA"
            elif label.lower() in ["sigma_v", "sigma_v_hanna", "sigma_v_irwin"]:
                name = "SigV"
            elif label.lower() in ["sigma_w", "sigma_w_hanna", "sigma_w_irwin"]:
                name = "SigW"
            elif label.lower() in ["tly", "tly_hanna", "tly_irwin", "tl_y", "tl_y_hanna", "tl_y_irwin"]:
                name = "TLY"
            elif label.lower() in ["tlz", "tlz_hanna", "tlz_irwin", "tl_z", "tl_z_hanna", "tl_z_irwin"]:
                name = "TLZ"
            elif label.lower() in ["u", "zonalwind", "zonal_wind"]:
                name = "VitU"
                u_list = met_dic[label]
            elif label.lower() in ["v", "meridionalwind", "meridional_wind"]:
                name = "VitV"
                v_list = met_dic[label]
            elif label.lower() in ["wind", "speed", "wind_speed", "vent", "vitesse"]:
                wind_list = met_dic[label]
            elif label.lower() in ["direction", "angle", "azimut"]:
                angle_list = met_dic[label]

            if name in self.variable2D or label in self.variable3D:
                field_dic[name] = met_dic[label]

        if v_list == [] and u_list != []:
            if wind_list == []:
                print("On suppose que \'u\' est le label pour la vitesse du vent")
                wind_list = u_list

        # Calcul de (u,v) connaissant la vitesse et la direction du vent
        if angle_list != [] and wind_list != []:
            u_list, v_list = convertWind(wind_list, angle_list)
            field_dic["VitU"] = u_list
            field_dic["VitV"] = v_list

        # Remplissage des champs météo
        print("Remplissage des champs météo pour les variables", field_dic.keys())
        self.fillMeteoField(field_dic)

        if angle_list != [] and wind_list != []:
            self.wind = np.zeros(self.variables["VitU"].shape)
            self.direction = np.zeros(self.variables["VitU"].shape)
            for t in range(self.wind.shape[0]):
                self.wind[t].fill(wind_list[t])
                self.direction[t].fill(angle_list[t])
        else:
            self.computeWind()


    ##############################
    # MANIPULATION DES MAILLAGES #
    ##############################


    def createPointSet1D(self, x_width, y_width, z_list):
        """
        Création de maillage 1D (1 seule maille horizontale + 1 profil vertical)
        """
        x = np.array([-x_width/2., x_width/2.])
        y = np.array([-y_width/2., y_width/2.])
        x, y, z = utils.create_3D_grid(x, y, z_list)
        point_index = self.createPointSet(x, y, z, [], "", "maillage 1D")


    ##########################
    # MANIPULATION DES DATES #
    ##########################


    def getDateList(self):
        """
        Calcule la liste de dates météo
        @return: la liste de dates
        @rtype: list
        """
        time_list = self.variables['TimeMeteo']
        date_ref = utils.string_to_datetime_fr(self.variables['TimeRef'])
        date_list = [date_ref + datetime.timedelta(seconds = float(t)) for t in time_list]
        return date_list


    def setTimeList(self, time_list, index=0):
        """
        Modification de la liste d'instants météo (sans modification du TimeRef)
        @param time_list: Liste des nouveaux instants météo
        @type time_list: float list
        """
        varkey = 'TimeMeteo'
        dimkey = 'NTimeMeteo'

        # Dimension
        self.dimensions[dimkey] = len(time_list)

        # Si les variables n'existent pas encore, tout est rajouté aux dictionnaires
        if varkey not in self.variables.keys():
            attr = {"long_name": "Instants meteo",
                    "units": "s"}

            self.createVariable(varkey, np.array(time_list, dtype='d'), (dimkey,), attr, 'd')
        else:
            self.variables[varkey] = np.array(time_list, dtype='d')

    def truncateMeteo(self, date_beg, date_end):
        """
        Troncature de la meteo suivant les dates specifiées.
        @param date_beg: Début météo.
        @type date_beg: datetime
        @param date_end: Fin du météo.
        @type date_end: datetime
        """
        # Recherche des indices de début et de fin
        dates = self.getDateList()
        ind_beg, ind_end = utils.truncateDates(date_beg, date_end, dates)
        new_dates = dates[ind_beg:ind_end]

        # Modification de la liste de dates et du TimeRef et de la dim associée
        self.setDateList(new_dates, True)
        self.dimensions["NTimeMeteo"] = len(new_dates)

        # Troncature de tous les champs météo
        for var in self.variable2D:
            self.variables[var] = self.variables[var][ind_beg:ind_end,:,:]
        for var in self.variable3D:
            self.variables[var] = self.variables[var][ind_beg:ind_end,:,:,:]

    ##########################
    # AJOUT DE DONNEES METEO #
    ##########################


    def addMeteoField(self, field_dic, field_attr = {}, index=0):
        """
        Ajout de champs météo qui sont déjà dans des tableaux de la bonne dimension.
        @param field_dic: dictionnaire dont les clés sont les noms des champs et les valeurs sont les tableaux
        @type field_dic: dictionnaire {champ: tableau} avec tableau de taille (Nt, Nz, Ny, Nx) ou (Nt, Ny, Nx)
        @param field_attr: dictionnaire contenant les attributs. Si vide, on gardera le dico créé à l'initialisation. (défaut: {})
        @type field_attr: dico contenant les dico d'attributs des champs
        @param index: indice du maillage associé
        @type index: int (défaut: 0)
        """
        # Maillage de référence
        self.globalAttr["Meteo_RefPointsSet"] = str(index)

        for var, value in iter(field_dic.items()):
            # Champs 3D
            if len(value.shape) == 4 and var in self.variable3D:
                vardim = ('NTimeMeteo', 'DimK'+str(index), 'DimJ'+str(index), 'DimI'+str(index))
            # Champs 2D
            elif len(value.shape) == 3 and var in self.variable2D:
                vardim = ('NTimeMeteo', 'DimJ'+str(index), 'DimI'+str(index))
            else:
                print("Le champ ", var, "a pour dimensions", value.shape)
                raise Exception("Tous les champs meteo doivent avoir la dimension (Nt, Nz, Ny, Nx) ou (Nt, Ny, Nx)")

            # Dimensions
            for ind, dim in enumerate(value.shape):

                # Si la dimension n'existe pas, exception (il faut créer le maillage et la liste d'instants avant)
                if vardim[ind] not in self.dimensions.keys():
                    raise Exception("Le maillage et la liste d'instants, et leurs dimensions, doivent exister!")

                # Sinon, on vérifie la compatibilité des tailles avec les dimensions
                elif self.dimensions[vardim[ind]] != value.shape[ind]:
                    print("La variable", var, "a pour dimension", ind, ":",  value.shape[ind],\
                        "et la dimension", vardim[ind], "vaut", self.dimensions[vardim[ind]])
                    raise Exception("Taille de tableau incompatible avec les dimensions de l'instance meteo")
                else:
                    pass

            # Création de la variable
            # print("Ajout de la variable", var)
            vartype = value.dtype
            if var in field_attr.keys():
                self.createVariable(var, value, vardim, field_attr[var], vartype)
            else:
                self.createVariable(var, value, vardim, {}, vartype)


    def fillMeteoField(self, field_dic, index=0):
        """
        Remplissage de champs météo avec des valeurs (le maillage est déjà créé et la liste d'instants aussi)
        """
        Nt = self.dimensions['NTimeMeteo']
        Nz = self.dimensions['DimK'+str(index)]
        Ny = self.dimensions['DimJ'+str(index)]
        Nx = self.dimensions['DimI'+str(index)]
        for var, value in iter(field_dic.items()):
            if var in self.variable3D:
                field_array = np.zeros((Nt, Nz, Ny, Nx), dtype='d')
            elif var in self.variable2D:
                field_array = np.zeros((Nt, Ny, Nx), dtype='d')
            else:
                raise Exception("La variable " + var + " est inconnue")

            # Remplissage de la même valeur à tous les pas de temps
            if np.isscalar(value):
                if utils.is_num(value):
                    # print("Remplissage du tableau", var, "avec la valeur", value)
                    field_array.fill(value)
            else:
                value = np.array(value)
                # Tableau d'1 seule dimension
                if len(value.shape) == 1:
                    # Si c'est 1 seule valeur, on fait comme si c'était un scalaire et on remplit le tableau avec
                    if value.shape[0] == 1:
                        field_array.fill(value[0])
                    # Sinon, c'est une liste de valeurs dans 1 dimension du tableau (suivant t ou z)
                    elif value.shape[0] ==  field_array.shape[0]:
                        for t in range(value.shape[0]):
                            field_array[t] = value[t]
                    elif value.shape[0] ==  field_array.shape[1]:
                        for z in range(value.shape[0]):
                            field_array[:,z,...] = value[z]
                    else:
                        raise Exception("La variable " + var + " a une liste de valeur de taille " + str(value.shape[0]) + " qui ne correspond pas a une dimension reconnue des champs meteo")

                # Tableau de 2 dimensions (t, z)
                elif len(value.shape) == 2:
                    if value.shape[0] == field_array.shape[0] and value.shape[1] == field_array.shape[1]:
                        for t in range(value.shape[0]):
                            for z in range(value.shape[1]):
                                field_array[t,z,...] = value[t,z]
                    # Sinon, c'est une liste de valeurs dans 1 dimension du tableau (suivant t ou z)
                    elif value.shape[0] == field_array.shape[0] and value.shape[1] == 1:
                        for t in range(value.shape[0]):
                            field_array[t] = value[t,0]
                    elif value.shape[0] ==  1 and value.shape[1] == field_array.shape[1]:
                        for z in range(value.shape[1]):
                            field_array[:,z,...] = value[0,z]
                    else:
                        raise Exception("La variable " + var + " a une taille " + str(value.shape) + " qui ne correspond pas a une dimension reconnue des champs meteo")

            field_dic[var] = field_array

        # Ajout des champs meteo à la bonne dimension
        self.addMeteoField(field_dic, {}, index)


    def setMeteoTimeStep(self, field_dic, time_step):
        """
        Modification de la valeur des champs meteo à un pas de temps donné
        """
        # Vérification de l'indice de pas de temps
        Nt = self.dimensions['NTimeMeteo']
        if time_step < -1 or time_step >= Nt:
            raise Exception("Le pas de temps " + str(time_step) + " n'est pas compris dans le nombre de paliers meteo")

        for var, value in iter(field_dic.items()):
            if value.shape != self.variable[var].shape[1:]:
                raise Exception("La taille du champ meteo " + var + " n'est pas compatible avec les dimensions deja existantes")
            else:
                self.variable[var][time_step] = value



    def addMeteoTimeStep(self, field_dic, delta_t):
        """
        Ajout d'un pas de temps meteo delta_t après le dernier pas de temps
        """
        # Modification de la liste de paliers temporels et du NTimeMeteo
        date_list = self.getDateList()
        date_list.append(date_list[-1] + datetime.timedelta(seconds=delta_t))
        self.setDateList(date_list)

        # Agrandissement des tableaux
        for var, value in iter(field_dic.items()):
            value = expand_dims(value, axis=0)
            self.variables[var] = concatenate(self.variables[var], value, axis=0)
            print("New shape:", self.variables[var].shape)
