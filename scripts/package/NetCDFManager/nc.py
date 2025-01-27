#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

import sys
import os
from netCDF4 import Dataset
import numpy as np
import datetime
from . import utils


#############
# CLASSE NC #
#############


class NC:
    """
    Manipulation de fichiers NetCDF (lecture, écriture, recopie).
    """
    def __init__(self, fileName="", data_type='d'):
        """
        Initialise la classe NC.
        Récuperation de toutes les données d'un fichier NetCDF:
        * attributs globaux
        * dimensions
        * variables
        * attributs des variables
        Stockage dans des dictionnaires.
        @param fileName: nom du fichier NetCDF
        @type fileName: string
        @param data_type: type des données susceptibles d'être lues ('d' ou 'f') (défaut: 'd')
        @type data_type: char
        """
        # Nom
        self.file = fileName
        self.name = os.path.basename(self.file).rstrip(".nc")

        # Attributs globaux
        self.globalAttr = {}
        self.globalAttr['Convention'] = "IRSN V1.0"
        self.globalAttr['GeoPointSetRef_Proj'] = "epsg:32630"
        self.globalAttr['GeoPointSetRef'] = "CARTO"

        # Dimensions et variables
        self.dimensions = {}
        self.dimensions['NMaxChar'] = 64
        self.dimensions['NCharDate'] = 20
        self.variables = {}

        # Attributs des variables
        self.variableAttr = {}
        self.variableDim = {}
        self.variableType = {}

        # Lecture des variables si le fichier existe
        if fileName != "":
            self.read_variables()


    def read_variables(self):
        """
        Lecture des variables du fichier NetCDF
        """
        # Lecture du fichier netcdf.
        fileNc = Dataset(self.file, 'r')

        # Dimensions (dictionnaire)
        self.dimensions = {}
        for key in fileNc.dimensions.keys():
            self.dimensions[key] = len(fileNc.dimensions[key])

        # Attributs globaux (hors attributs de base de la classe)
        self.globalAttr = fileNc.__dict__

        # Variables
        variables = fileNc.variables
        for var in variables.keys():
            self.read_variable(var, variables)

        fileNc.close()


    def read_variable(self, var, variables={}):
        """
        Lecture d'une variable donnée
        @param var: nom de la variable
        @type var: string
        @param variables: dictionnaire des variables NetCDF (défaut {}=
        @type variables: dic
        """
        # Lecture du fichier netcdf si besoin

        if variables != {} and var not in variables.keys():
                print("Variable", var, "introuvable")
                pass
        elif var in self.variables.keys():
            return self.variables[var]
        else:
            if variables == {}:
                fileNc = Dataset(self.file, 'r')
                variables = fileNc.variables
                print(variables.keys())

            # Différents types
            data_type = variables[var].dtype
            try:
                if var.startswith("IsoId"):
                    self.variables[var] = np.array(variables[var].getValue(), dtype='i')
                elif var.startswith("NPoint") or var.startswith("NResult") or var.startswith("NSource") or var.startswith("TimeBeginSource") or var.startswith("NCsx"):
                    self.variables[var] = variables[var].getValue()[0]
                else:
                    self.variables[var] = np.array(variables[var], dtype=data_type)
            except:
                self.variables[var] = np.array(variables[var])

            # Concaténation des listes de char pour obtenir des chaines de caractères
            if var.startswith("IsoName") or var.startswith("NamePts"):
                tab = self.variables[var]
                self.variables[var] = [filter(utils.isAcceptableChar, s.tostring())\
                                        for s in tab]
            if var == "TimeRef":
                tab = self.variables[var]
                self.variables[var] = utils.concat_str(tab)

            # Attributs des variables
            # dico avec les clés 'unit' et 'long_name'
            self.variableAttr[var] = variables[var].__dict__
            # Dimensions de la variable
            self.variableDim[var] = variables[var].dimensions
            # Type de la variable
            self.variableType[var] = variables[var].dtype

            if variables == {}:
                fileNc.close()
            return self.variables[var]


    # Création ou modification du TimeRef (partagé par les classes source, domain, meteo, result)

    def setTimeRef(self, date_ref):
        """
        Crée ou modifie le TimeRef du fichier NC
        @param date_ref: date de référence à utiliser pour le TimeRef
        @type date_ref: datetime
        """
        if "TimeRef" not in self.variables.keys():
            self.variableType["TimeRef"] = 'c'
            self.variableDim["TimeRef"] = ('NCharDate',)
            self.variableAttr["TimeRef"] = {'long_name': 'Date de reference',
                                            'units': 'jj/mm/aaaa hh:mm:ss'}

        time_ref = date_ref.strftime("%d/%m/%Y %H:%M:00")
        self.variables["TimeRef"] = time_ref
        print("Nouveau TimeRef", self.variables["TimeRef"])


    def setDate(self, date_beg, date_end, delta_t, set_time_ref=False, index=0):
        """
        Crée une liste de dates avec le pas de temps delta_t et appelle la méthode setDateList
        @param date_beg: date de début
        @type date_beg: datetime
        @param date_end: date de fin
        @type date_end: datetime
        @param delta_t: pas de temps de la liste de dates (secondes)
        @type delta_t: float
        @param index: indice associé à la liste à modifier
        @type index: int (défaut: 0)
        """
        Nt = (date_end - date_beg).days * 24 * 3600 + (date_end - date_beg).seconds
        Nt = int(Nt / delta_t) + 1
        date_list = [date_beg + datetime.timedelta(seconds=t*delta_t) for t in range(Nt)]
        self.setDateList(date_list, set_time_ref, index)
        return date_list


    def setDateList(self, date_list, set_time_ref=False, index=0):
        """
        Modification de la liste d'instants (avec/sans modification du TimeRef)
        @param date_list: Liste des dates
        @type date_list: datetime list
        @param index: indice associé à la liste à modifier
        @type index: int (défaut: 0)
        """
        # Ajout du TimeRef si besoin
        if "TimeRef" not in self.variables.keys() or set_time_ref:
            date_ref = date_list[0]
            self.setTimeRef(date_ref)
        else:
            date_ref = utils.string_to_datetime_fr(self.variables["TimeRef"])

        # Modification de la liste d'instants
        time_list = np.array([(d - date_ref).days * 24 * 3600 +  (d - date_ref).seconds for d in date_list])
        if hasattr(self, "setTimeList"):
            self.setTimeList(time_list, index)
        else:
            print("La classe ", self.__class__, "n'a pas d'attribut setTimeList")


    # Création d'un ensemble de points (partagé par les classes source, domain, meteo, result)

    def createPointSet(self, x, y, z, name_list = [], index="", mesh_name=""):
        """
        Modifie le maillage ou la liste de points, ou le rajoute dans le fichier
        @param x_list: coordonnées en x (taille (Nz, Ny, Nx) ou (Npts))
        @type x_list: float array
        @param y_list: coordonnées en y (taille (Nz, Ny, Nx) ou (Npts))
        @type y_list: float array
        @param z_list: coordonnées en z (taille (Nz, Ny, Nx) ou (Npts))
        @type z_list: float array
        @param name_list: liste des noms de balises: uniquement si liste de points (défaut: [])
        @type name_list: string list
        @param index: Indice de l'ensemble de points. Défaut: "" (le rajoute à la suite du fichier)
        @type index: int
        @param mesh_name: nom à donner à l'ensemble de points (attribut 'PointsSet_long_name') (défaut :"")
        Si défaut, le nom sera "balises" pour une liste de points et "maillage" pour un maillage 3D
        @type mesh_name: string
        """
        x = np.array(x)
        y = np.array(y)
        z = np.array(z)

        # Indice du nouvel ensemble de points
        if "NPointsSet" not in self.variables.keys():
            index = 0
            self.variables["NPointsSet"] = 1
            self.variableDim["NPointsSet"] = ()
            self.variableType["NPointsSet"] = 'i'
            self.variableAttr["NPointsSet"] = {"units": "",
                                               "long_name": "Nombre de maillage"}
        elif index == "":
            Np = int(self.variables["NPointsSet"])
            index = Np
            print("Indice du nouvel ensemble de points:", index)
            self.variables["NPointsSet"] = Np + 1

        # Dimensions
        if z.shape != x.shape or z.shape != y.shape:
            print(x.shape, y.shape, z.shape)
            raise Exception("createPointsSet: Les tailles de maillages ne sont pas identiques (taille (Nz, Ny, Nx))")

        if len(z.shape) == 3:
            self.dimensions["DimI" + str(index)] = x.shape[2]
            self.dimensions["DimJ" + str(index)] = y.shape[1]
            self.dimensions["DimK" + str(index)] = z.shape[0]
            point_type = "0"
            maillage = True
            if mesh_name == "":
                mesh_name = "maillage"
        elif len(z.shape) == 1:
            self.dimensions["DimNPts" + str(index)] = z.shape[0]
            point_type = "1"
            maillage = False
            if mesh_name == "":
                mesh_name = "balises"
        else:
            raise Exception("createPointsSet: Les tableaux doivent etre de dimension 1 ou 3")

        # Variables
        varlist = [x, y, z]
        varnames = ["Coord X", "Coord Y", "Coord Z"]
        vartype = 'd'
        if maillage:
            vardim = ('DimK' + str(index), 'DimJ' + str(index), 'DimI' + str(index))
        else:
            vardim = ('DimNPts' + str(index),)

        # On crée les variables CoordX, Y, Z, avec leurs dimensions et attributs
        for varname, var in zip(varnames, varlist):
            varattr = {"units": "m",
                       "long_name": varname}
            self.createVariable("".join(varname.split(" ")) + str(index), var, vardim, varattr, vartype)

        # Si c'est une liste de points, on rajoute le nom des points
        if not maillage:
            varattr["long_name"] = "Nom des points"
            varattr["units"] = ""
            vartype = 'c'
            if len(name_list) != z.shape[0]:
                print(len(name_list), z.shape[0])
                raise Exception("createPointsSet: La liste des noms de points et des coordonnees n'ont pas une taille identique")
            else:
                self.createVariable("NamePts" + str(index), name_list, ('DimNPts' + str(index), 'NMaxChar'), varattr, vartype)

        # Attributs globaux
        self.globalAttr["PointsSet_long_name" + str(index)] = mesh_name
        self.globalAttr["PointsSet_Type" + str(index)] = point_type
        self.globalAttr["PointsSet_IsMobile" + str(index)] = '0'

        return index


    def createVariable(self, var, value, vardim, varattr={}, vartype='d'):
        """
        Crée une variable de nom var, de valeur value, et la rajoute dans le dictionnaire variables
        Les dimensions de la variable sont données par le tuple vardim
        Les attributs sont donnés par le dictionnaire varattr
        """
        # Ajout variable
        self.variables[var] = value
        self.variableDim[var] = vardim
        self.variableType[var] = vartype

        if varattr == {} and var in self.variableAttr.keys():
            pass
        else:
            self.variableAttr[var] = varattr

        for dim in vardim:
            if dim not in self.dimensions.keys():
                print("Attention: la dimension", dim, "n'existe pas encore. Veuillez l'initialiser.")


    def copyVariable(self, var, NC_out, name_out=""):
        """
        Recopie une variable dans un objet de type NETCDFFile (valeur, dimensions, type et attributs)
        @param var: nom de la variable
        @type var: string
        @param NC_out: NETCDF output file
        @type NC_out: NETCDFFile
        @param name_out: nom de la variable de sortie (si différent de var)
        @type name_out: string
        """
        # print("# Copying variable", var)
        if name_out == "":
            name_out = var
        var_out = NC_out.createVariable(name_out, self.variableType[var], self.variableDim[var])

        # Conversions en liste de char avec la bonne dimension (transformation inverse de concat_str)
        if var == "TimeRef":
            var_out[:] = utils.str_to_char(self.variables[var], self.dimensions['NCharDate'])
        elif var.startswith("IsoName")  or var.startswith("NamePts"):
            char_iso = [utils.str_to_char(species, self.dimensions['NMaxChar']) for species in np.array(self.variables[var])]
            var_out[:] = np.array(char_iso)
        elif var.startswith("NCsx"):
            var_out[:] = self.variables[var]
        else:
            var_out[:] = np.array(self.variables[var])

        # Attributs des variables
        for name, value in iter(self.variableAttr[var].items()):
            setattr(var_out, name, value)
        NC_out.sync()


    def writeNC(self, fileName, mode = 'w'):
        """
        Ecriture dans un fichier au format netcdf.
        @param fileName: Nom du fichier.
        @type fileName: str
        @param mode: Mode d'écriture (défaut: w)
        @type mode: str
        """
        file_out = Dataset(fileName, mode)
        self.file = file_out

        # Dimensions
        for name, value in iter(self.dimensions.items()):
            file_out.createDimension(name, value)

        # Attributs globaux
        for name, value in iter(self.globalAttr.items()):
            setattr(file_out, name, value)

        # Variables
        for var in self.variables.keys():
            self.copyVariable(var, file_out)

        file_out.sync()
        file_out.close()
