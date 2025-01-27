#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from . import nc
import datetime
from netCDF4 import Dataset


#################
# CLASSE RESULT #
#################


class Result(nc.NC):
    """
    Manipulation fichiers de résultats (fichier nc).
    La classe Result dérive de la classe générique NC.
    """

    ######################
    # LECTURE DE DONNEES #
    ######################


    def __init__(self, fileName, read = False):
        """
        Initialise la classe Result, et lit les variables si demandé.
        Par défaut, ne lit que certaines variables (sinon il peut y avoir des problèmes de mémoire pour les trop gros fichiers)
        @param fileName: nom du fichier nc à lire
        @type fileName: string
        @param read: pour dire si les variables doivent toutes être lues (défaut: False)
        @type read: bool
        """

        # Initialisation à vide (pour éviter de tout charger en mémoire)
        nc.NC.__init__(self, "", 'd')
        self.file = fileName

        # Quelques attributs utiles
        fileNc = Dataset(fileName, 'r')

        # Dimensions (dictionnaire)
        self.dimensions = {}
        for key in fileNc.dimensions.keys():
            self.dimensions[key] = len(fileNc.dimensions[key])
        self.globalAttr = fileNc.__dict__

        # On ne lit pas toutes les variables
        variables = fileNc.variables
        variable_list = ["NResult", "NSource", "NPointsSet", "TimeRef"]
        for var in variable_list:
            self.read_variable(var, variables)

        # Liste d'isotopes
        for s in range(self.variables["NSource"]):
            var = "IsoNameListSource" + str(s)
            self.read_variable(var, variables)

        # Ensemble de point associé à chaque résultat
        for p in range(self.variables["NPointsSet"]):
            self.read_variable("CoordX" + str(p), variables)
            self.read_variable("CoordY" + str(p), variables)
            self.read_variable("CoordZ" + str(p), variables)

            # Si c'est une liste de points, on récupère le nom des stations
            if int(self.globalAttr["PointsSet_Type" + str(p)]) == 1:
                self.read_variable("NamePts" + str(p), variables)

        fileNc.close()


        # Dictionnaire destiné à recevoir les résultats
        self.data = {}


    def get_attributes(self, s=0, r=0):
        """
        Retourne quelques attributs associés au résultat r et à la source s
        """
        timeRef = self.variables["TimeRef"]
        time_list = self.variables["ResultTime" + str(s) + "-" + str(r)]

        # Ensemble de point correspondant au résultat
        p = int(self.globalAttr["Result_RefPointsSet" + str(r)])
        x = self.variables["CoordX" + str(p)][0]
        y = self.variables["CoordY" + str(p)][0]

        return timeRef, time_list, x, y


    def getDateList(self, r=0):
        """
        Calcule la liste de dates météo
        @return: la liste de dates
        @rtype: list
        """
        timeRef = self.variables["TimeRef"]
        time_list = self.variables["ResultTime" + str(r)]
        date_ref = string_to_datetime_fr(self.variables['TimeRef'])
        date_list = [date_ref + datetime.timedelta(seconds = float(t)) for t in time_list]
        return date_list


    #########################
    # MOYENNE DES RESULTATS #
    #########################


    def average_result(self, delta_t, file_av, res_type="consx", averaging_type="middle"):
        """
        Moyenne temporelle des résultats sur le pas de temps delta_t
        Attention: ne marche que sur les listes de points, pas sur les maillages
        @param delta_t: plage de temps sur laquelle est faite la moyenne (secondes)
        @type delta_t: float
        @param file_av: fichier nc de resultats contenant les valeurs moyennes
        @type file_av: string
        @param res_type: resultats que l'on veut moyenner (px ou consx ou all) (défaut: consx)
        @type res_type: string
        @param averaging_type: est-ce qu'on veut la moyenne sur la plage avant la date (end), après la date (start) ou entre date - delta_t/2 et date + delta_t/2 (middle) (défaut: middle)
        @type averaging_type: string
        """
        print("type de resultat que l'on veut moyenner:", res_type)
        if not hasattr(self,"variables"):
            self.read_variables('d')

        # Liste des dates où l'on a les résultats
        time_list_old  = self.variables['ResultTime0']
        date_ref = string_to_datetime_fr(self.variables["TimeRef"])
        old_dates = [date_ref + datetime.timedelta(seconds = float(t)) for t in time_list_old]

        # Nouvelle liste de dates
        date_beg = old_dates[0]
        Nt = 1 + int(((old_dates[-1] - old_dates[0]).days * 24 * 3600. +  (old_dates[-1] - old_dates[0]).seconds) / delta_t)
        new_dates = [date_beg + datetime.timedelta(seconds=delta_t * i) for i in range(Nt)]
        time_list = array([(d - date_ref).days * 24 * 3600 +  (d - date_ref).seconds for d in new_dates])
        Nt = len(time_list)

        # Species
        Ns = self.dimensions['NIsoSource0']
        # Cas des listes de points:
        if int(self.globalAttr['PointsSet_Type0']) == 1:
            Npt = self.dimensions['DimNPts0']
        # Cas des maillages
        else:
            print("La fonction average_result n'est utilisable que pour les listes de points")
            sys.exit(1)

        # Calcul des moyennes temporelles pour toutes les variables
        variables = {}
        for var in self.variables.keys():
            print("\n###", var)
            if var == 'ResultTime0':
                variables[var] = time_list
            elif var.startswith("Csx") or var.startswith("Result"):
                # Taille des tableaux (Nt, Npt, Ns) si resultat px, (Nt, Npt) si resultat consx
                if var.startswith("Result"):
                    variables[var] = zeros((Nt, Npt, Ns), dtype = self.variableType[var])
                else:
                    variables[var] = zeros((Nt, Npt), dtype = self.variableType[var])

                # Si l'on ne veut pas moyenner, on prend la valeur du resultat
                # au point le plus proche de la date de sortie
                if (var.startswith("Csx") and res_type == "px"):
                    for t, date in enumerate(new_dates):
                        ind = find_nearest_date_beg(date, old_dates)
                        variables[var][t] = self.variables[var][ind, :]

                elif (var.startswith("Result") and res_type == "consx"):
                    for t, date in enumerate(new_dates):
                        ind = find_nearest_date_beg(date, old_dates)
                        variables[var][t] = self.variables[var][ind, :, :]

                # Sinon, on fait les moyennes
                elif (var.startswith("Csx") and res_type == "consx") \
                        or (var.startswith("Result") and res_type == "px") or res_type == "all":
                    print("Moyenne pour la variable", var)
                    for p in range(Npt):
                        for t, date in enumerate(new_dates):
                            print("\n#", date.strftime("%Y-%m-%d-%H:%M"))
                            if averaging_type == "middle":
                                date_min = date - datetime.timedelta(seconds=delta_t/2.)
                                date_max = date + datetime.timedelta(seconds=delta_t/2.)
                            elif averaging_type == "start":
                                date_min = date
                                date_max = date + datetime.timedelta(seconds=delta_t)
                            elif averaging_type == "end":
                                date_min = date - datetime.timedelta(seconds=delta_t)
                                date_max = date
                            else:
                                raise IOerror("averaging type must be middle, start or end but is", averaging_type)

                            mean_value = 0
                            Nmean = 0
                            for ind, d in enumerate(old_dates):
                                if d >= date_min and d < date_max:
                                    print(d.strftime("%Y-%m-%d-%H:%M"))
                                    mean_value += self.variables[var][ind, p]
                                    Nmean += 1
                                elif d >= date_max:
                                    break
                            if Nmean != 0:
                                print("Nombre de valeurs utilisees pour la moyenne:", Nmean)
                                variables[var][t, p] = mean_value / Nmean
                else:
                    print("result_type ", res_type, "inconnu (result_type = px, consx ou all)")
            else:
                variables[var] = self.variables[var]

        self.variables = variables
        self.dimensions['NTimeResult0'] = len(time_list)
        self.file = file_av
        self.writeNC(file_av)


#############################
# MODIFICATION FORMES IODES #
#############################


def split_iodine(result_file, file_out, ref_file, gas_percent = 2./3.):
    res = nc.NC(result_file)
    species_list = res.variables['IsoNameListSource0']

    # Pour tous les isotopes de l'iode, on rajoute la forme gazeuse
    ind_iodine = []
    iodine_list = []
    for s, species in enumerate(species_list):
        if species.split("-")[0] == "I":
            ind_iodine.append(s)
            iodine_list.append(species + "_I")

    # Nouvelle liste d'isotopes: on cherche les ID correspondantes
    species_list = species_list + iodine_list
    id_list = []
    for s, species in enumerate(species_list):
            ref = open(ref_file, 'r')
            for line in ref.xreadlines():
                l = line.split()
                if len(l) > 2:
                    if l[1] == species:
                        id_list.append(int(l[0]))
                        break
            ref.close()

    Ns = len(species_list)
    Ni = len(ind_iodine)
    res.variables['IsoNameListSource0'] = array(species_list)
    res.variables['IsoIdListSource0'] = array(id_list, dtype="i")
    res.dimensions["NIsoSource0"] = Ns
    print("Nouveau nombre d'isotopes:", Ns)
    print("Nombre d'isotopes rajoutes:", Ni)


    # Pour toutes les variables de type résultat, on partage entre la forme gazeuse (2/3) et aerosol (1/3)
    for var in res.variables.keys():
        if var.startswith("Result") and var != "ResultTime0":
            print("\n##",var)
            l = list(res.variables[var].shape)
            l[-1] = Ns
            data = zeros(tuple(l), dtype=res.variables[var].dtype)
            print(data.shape)

            # On parcourt les "anciennes" espèces (aerosol)
            for s in range(Ns - Ni):
                print(species_list[s])
                # Si c'est de l'iode, on multiplie par 1/3 et on met le reste à l'indice du gaz
                if s in ind_iodine:
                    ind = ind_iodine.index(s)
                    print(species_list[Ns - Ni + ind])
                    if len(data.shape) == 3:
                        data[:,:,s] = (1. - gas_percent) * res.variables[var][:,:,s]
                        data[:,:,Ns - Ni + ind] = gas_percent * res.variables[var][:,:,s]
                    else:
                        data[:,:,:,:,s] = (1. - gas_percent) * res.variables[var][:,:,:,:,s]
                        data[:,:,:,:,Ns - Ni + ind] = gas_percent * res.variables[var][:,:,:,:,s]
                # Si ce n'est pas de l'iode, on recopie tel quel le résultat
                else:
                    if len(data.shape) == 3:
                        data[:,:,s] = res.variables[var][:,:,s]
                    else:
                        data[:,:,:,:,s] = res.variables[var][:,:,:,:,s]

            # data est donc la nouvelle variable résultat
            res.variables[var] = data
    # On réécrit tout
    res.writeNC(file_out)


###########################
# SOMMATION DES RESULTATS #
###########################


def add_results(results, file_sum, percent=1):
    # Dico de variables sommées
    variables = {}

    # Sommation de tous les résultats
    for result in results:
        print("\nAjout source ", result)
        nc = nc.NC(result)
        for var in nc.variables.keys():
            if var.startswith("Result") or var.startswith("Csx"):
                if not var.startswith("ResultTime"):
                    print("Sommation pour la variable ", var, nc.variableDim[var])
                    try:
                        variables[var] += percent * nc.variables[var]
                    except KeyError:
                        variables[var] = percent * nc.variables[var]
                else:
                    variables[var] = nc.variables[var]
            else:
                variables[var] = nc.variables[var]

    # On écrase les variables du dernier fichier lu par la somme
    nc.variables = variables

    sum_path = file_sum.split("result")[0]
    if not os.path.isdir(sum_path):
        os.makedirs(sum_path)
    print("\n ###Ecriture fichier somme:", file_sum)
    nc.writeNC(file_sum)
    return 0
