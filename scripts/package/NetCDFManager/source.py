#!/usr/bin/env python
# -*- coding: iso-8859-15 -*-

from . import nc
from .utils import *
import datetime
import numpy as np
from functools import reduce
try:
    import pylab
except:
    "Import du module pylab impossible. Ne pas utiliser les fonctions de type plotRateSpecies"


#######################################################
# FONCTIONS GÉNÉRIQUES POUR TRACER DES TERMES SOURCES #
#######################################################

def addSourcePlot(tsFile, label, speciesList, dateDic={}, rateDicSpecies={}, cumulPath="."):
    """
    Fonction qui ajoute un terme source dans les dictionnaires dateDic et rateDicSpecies
    Ces dictionnaires seront pris en entrée de plotRateSpecies pour affichage
    @param tsFile: nom du fichier contenant la source à rajouter
    @type tsFile: string
    @param label: nom de la source associée (à utiliser sur la figure)
    @type label: string
    @param speciesList: liste des radionucléides à tracer
    @type speciesList: list of string
    @param dateDic: Dictionnaire à remplir avec les dates du rejet
    @type dateDic: dic
    @param rateDicSpecies: Dictionnaire à remplir avec les débits de rejet pour chaque espèce
    @type rateDicSpecies: dic
    @param cumulPath: chemin du fichier où le cumul du terme source sera écrit
    @type cumulPath: string
    """
    ts = Source(tsFile)
    dates = ts.getSourceDate()
    date_beg = ts.getSourceBeginDate()
    dateDic[label] = [date_beg] + dates[:-1]
    dateDic[label].append(dateDic[label][-1] + datetime.timedelta(minutes=1))

    for species in speciesList:
        try:
            rateDicSpecies[species][label] = ts.getSpeciesRate(species)
        except KeyError:
            rateDicSpecies[species] = {label: ts.getSpeciesRate(species)}
        rateDicSpecies[species][label] = list(rateDicSpecies[species][label])
        rateDicSpecies[species][label].append(0)
        # Affichage cumul pour vérification
        cumul = ts.computeCumul()
        cumulFile = "cumul_" + label + ".txt"
        ts.writeCumul(os.path.join(cumulPath, cumulFile))


def plotRateSpecies(dates, debit, name, species, figure_path=".", dbeg="", dend="",
                     fillDic={}, scaling=1, english=False):
    """
    Trace le débit (instantané ou cumulé) aux dates spécifiées
    @param dates: dico de liste de dates auxquelles les débits sont donnés (débuts de paliers)
    @type dates: dic
    @param debit: dico de listes de débits à tracer (même longueur que dates)
    @type debit: dic
    @param name: nom utilisé dans le titre et le nom de la figure ("cumul" ou "débit")
    @type name: string
    @param species: nom de l'espèce (pour titre et nom de la figure)
    @type species: string
    @param figure_path: chemin des figures
    @type figure_path: string
    @param dbeg: date de début du tracé
    @type dbeg: string
    @param dend: date de fin du tracé
    @type dend: string
    @param fillDic: Si vrai, alors le tracé du débit est rempli (vrai/faux pour chaque simulation)
    @type fillDic: bool dic
    @param scaling: Facteur multiplicatif appliqué au débit (ex: 10^14) pour lisibilité
    @type scaling: int
    @param english: Si vrai, alors la légende est en anglais (sinon, français)
    @type english: bool
    """
    clf()
    fig = gcf()
    ax = fig.add_axes([0.1, 0.2, 0.75, 0.75])
    color_list = ["k", "r", "g", "b", "m", "c", "#330066", "#FF6600", "#663300", "#3366FF", "#003333", "#FF99CC"]
    Ns = len(color_list)
    labels = sort(debit.keys())

    # Dates de début et de fin des tracés
    if dbeg!="" and dend != "":
        date_beg = string_to_datetime(dbeg)
        date_end = string_to_datetime(dend)
        figure_path = os.path.join(figure_path, date_beg.strftime("%d") + "au" + date_end.strftime("%d"))

    print("Figures des rejets dans", figure_path)
    # Boucle sur les simulations à tracer
    for k, label in enumerate(labels):
        # Paliers
        dates_list = []
        debits_list = []
        for ind, d in enumerate(dates[label][:-1]):
            dates_list.append(d)
            delta =dates[label][ind + 1] - d
            dates_list.append(d + delta - datetime.timedelta(seconds=1))
            debits_list.append(debit[label][ind])
            debits_list.append(debit[label][ind])

        if dbeg!="" and dend != "":
            ibeg, iend = truncateDates(date_beg, date_end, dates_list)
            if ibeg != -999 and iend != -999:
                dates_list = dates_list[ibeg:iend]
                debits_list = debits_list[ibeg:iend]
            # Cas où les dates ne sont pas comprises dans la plage de rejet: on met des zéros
            else:
                dates_list = [date_beg, date_end]
                debits_list = [0, 0]

        x = [date2num(d) for d in dates_list]
        y = np.array(debits_list) * scaling
        c = color_list[k%Ns]
        label_name = reduce(lambda x,y:x+" "+y, [str(li) for li in label.split("_")])

        if label in fillDic.keys() and fillDic[label]:
            plt = plot_date(x, y, "w-", color=c, ls='--',\
                                linewidth=2, label=unicode(label_name))
            fill_between(x, 0, y, facecolor=c)
        else:
            plt = plot_date(x, y, "w-", color=c, ls='-',\
                                linewidth=2, label=unicode(label_name))

    # Fin de la boucle

    # Légende
    legend(loc='best')

    # Axe des abscisses (date)
    if dbeg!="" and dend != "":
        xlim(date2num(date_beg), date2num(date_end))
    gca().xaxis.set_major_formatter(DateFormatter('%d/%m %Hh'))
    setp(gca().get_xticklabels(), 'rotation', 45, \
             'horizontalalignment', 'right', fontsize=7)
    if english:
        xlabel("Date and time")
    else:
        xlabel("Date et heure")


    # Unité
    unit = ""
    if name.lower() == "debit":
            unit = "Bq/s"
    elif name.lower() == "cumul":
        unit = "Bq"

    if scaling != 1:
        unit = r" ($\times 10^{" + str(int(-log10(scaling))) + "}$ " + unit + ")"
    else:
        unit = " (" + unit + ")"

    # Titre et axe des ordonnées
    task_name = name[0].upper() + name[1:].lower()
    if task_name == "Debit":
        if english:
            task_name = u"Release rate"
        else:
            task_name = u"Débit"
    ylabel(task_name + " " + unit)
    species_name = species

    # if species_name == "Te-132":
    #     species_name = "Te-132 + I-132"
    if species_name.lower() == "iodes":
        species_name = "Iodine"
    if species_name.lower() == "cesiums":
        species_name = "Cesium"
    if species_name.lower() == "gr":
        species_name = "Noble gases"
    elif species_name.lower() == "non_gr":
        if english:
            species_name = "Other than noble gases"
        else:
            species_name = "Autres que gaz rares"
    elif species_name.lower() == "tous_iso" or species_name.lower() == "tous_rn":
        if english:
            species_name = "All species"
        else:
            species_name = "Tous isotopes"
    title(unicode(species_name))
#    title("Release amount", weight='bold')
    title(unicode(task_name + " de rejet de " + species_name))

    # Savefig
    if not os.path.isdir(figure_path):
        os.makedirs(figure_path)
    savefig(os.path.join(figure_path, name +  "_" + species), facecolor='w', \
                bbox_inches="tight", pad_inches=0.1, dpi=300)


def getFamilySpecies(species_list, family):
    """
    Pour une famille donnée, retourne la liste d'espèces correspondantes
    @param species_list: liste d'isotopes de départ
    @type species_list: list
    @param family: la famille demandée ('GR', 'iodes', 'cesiums', 'non_GR')
    @type family: string
    @return: liste des noms d'espèces
    @rtype: list
    """
    species_GR = [s for s in species_list if 'Xe' in s or 'Kr' in s]
    species_other = [s for s in species_list if s not in species_GR]
    species_Cs = [s for s in species_list if 'Cs' in s]
    species_I = [s for s in species_list if 'I' in s]

    if family.lower() == 'gr' or family.lower() == 'gaz_rare' or \
            family.lower() == 'gaz_rares':
        return species_GR
    elif 'iode' in family.lower():
        return species_I
    elif 'cesium' in family.lower() or 'caesium'  in family.lower():
        return species_Cs
    elif 'non_gr' in family.lower() or 'non_gaz_rare' in family.lower() \
            or 'autres_que_gr'in family.lower():
        return species_other
    elif 'tous_iso' in family.lower() or 'tous_rn' in family.lower():
        return species_list
    else:
        print('Famille ', family, 'inconnue. Les familles possibles sont GR, iodes, cesiums, non_GR.')


#################
# CLASSE SOURCE #
#################


class Source(nc.NC):
    """
    Manipulation terme source (fichier nc).
    La classe Source dérive de la classe générique NC.
    """
    def __init__(self, fileName=""):
        """
        Initialise la classe Source.
        Récuperation des caracteristiques du terme source.

        """
        nc.NC.__init__(self, fileName, 'd')

        # Dictionnaire destiné à recevoir des données non écrites dans le fichier netcdf
        self.data = {}

    def setSourceHeight(self, height, index=0):
        """
        Hauteur de rejet
        @param height: Hauteur de rejet.
        @type height: float
        @param index: Indice de la source. Défaut: 0
        @type index: int
        """
        self.variables['CoordZ'+str(index)] = height
        self.name = self.name + "_%02d"%int(height)


    def setCoord(self, coords, index=0):
        """
        Coordonnées
        @param coords: (x, y, z)
        @type coords: tuple
        @param index: Indice de la source. Défaut: 0
        @type index: int
        """
        self.variables['CoordZ'+str(index)] = coords[2]
        self.variables['CoordY'+str(index)] = coords[1]
        self.variables['CoordX'+str(index)] = coords[0]

    def setSourceDimHeight(self, dimZ, index=0):
        """
        Taille suivant Z (source volumique)
        @param dimZ: dimension suivant Z.
        @type dimZ: float
        @param index: Indice de la source. Défaut: 0
        @type index: int
        """
        self.variables['DimZSource'+str(index)] = dimZ
        self.variableType['DimZSource'+str(index)] = 'd'
        self.variableDim['DimZSource'+str(index)] = ()
        self.variableAttr['DimZSource'+str(index)] = {'long_name': 'Dimension de la source selon z', 'units': 'm'}


    ##############################
    # GESTION DES DATES DE REJET #
    ##############################

    def getDateList(self, index=0):
        date_beg = self.getSourceBeginDate(index)
        return [date_beg] + self.getSourceDate()


    def getSourceDate(self, index=0):
        """
        Calcule la liste de dates auxquelles les débits sont donnés, et la stocke dans self.data
        @param index: Indice de la source. Défaut: 0
        @type index: int
        @return: la liste de dates de rejet
        @rtype: list
        """
        time_list = self.variables['TimeSource' + str(index)]
        date_ref = string_to_datetime_fr(self.variables['TimeRef'])
        #print(date_ref.strftime("%Y-%m-%d %H"))
        dates = [date_ref + datetime.timedelta(seconds = float(t)) for t in time_list]
        #print(dates[0].strftime("%Y-%m-%d %H"))
        self.data['DateSource' + str(index)] = dates
        return self.data['DateSource' + str(index)]


    def setTimeList(self, time_list, index=0):
        """
        Modification des instants de rejet: date de début de rejets et liste de fins de paliers
        @param time_list: Liste des nouveaux instants de rejet (de taille NTimeSource + 1 car la première valeur est la date de début de rejet)
        @type time_list: float list
        @param index: Indice de la source. Défaut: 0
        @type index: int
        """
        # Instant de début de rejet
        varkey = "TimeBeginSource" + str(index)
        if varkey not in self.variables.keys():
            attr = {"long_name": "Instant de debut de rejet",
                    "units": "s"}
            self.createVariable(varkey, time_list[0], (), attr, 'd')
        else:
            self.variables[varkey] = time_list[0]

        # Liste de fin de palier
        varkey = 'TimeSource' + str(index)
        dimkey = 'NTimeSource' + str(index)

        # Dimension
        self.dimensions[dimkey] = len(time_list[1:])

        # Si les variables n'existent pas encore, tout est rajouté aux dictionnaires
        if varkey not in self.variables.keys():
            attr = {"long_name": "Instants des fins de paliers de rejet",
                    "units": "s"}

            self.createVariable(varkey, np.array(time_list[1:], dtype='d'), (dimkey,), attr, 'd')
        else:
            self.variables[varkey] = np.array(time_list[1:], dtype='d')


    def getSourceBeginDate(self, index=0):
        """
        Calcule la date de début de la source
        @param index: Indice de la source. Défaut: 0
        @type index: int
        @return: la date de début de rejet
        @rtype: list
        """
        tbegsource = self.variables['TimeBeginSource' + str(index)]
        date_ref = string_to_datetime_fr(self.variables['TimeRef'])
        date_beg = date_ref + datetime.timedelta(seconds = float(tbegsource))
        return date_beg


    def truncateSource(self, date_beg, date_end, index=0):
        """
        Troncature du rejet suivant les dates specifiées, pour la source d'indice index.
        @param date_beg: Début du rejet.
        @type date_beg: datetime
        @param date_end: Fin du rejet.
        @type date_end: datetime
        @param index: Indice de la source. Défaut: 0
        @type index: int
        """
        # Paramètres de la source
        time_list_old = self.variables['TimeSource' + str(index)]
        time_begin_old = float(self.variables['TimeBeginSource' + str(index)])
        debit_old = self.variables['DebitSource' + str(index)]

        # Liste de dates correspondant à la source
        dates = self.getSourceDate(index)

        # Recherche des indices de début et de fin
        ind_beg, ind_end = truncateDates(date_beg, date_end, dates)

        # Nouveaux paramètres de la source
        time_list = np.array(time_list_old[ind_beg+1:ind_end+1])
        self.data["DateSource" + str(index)] = dates[ind_beg+1:ind_end+1]
        self.variables['TimeSource' + str(index)] = time_list
        self.dimensions['NTimeSource' + str(index)] = len(time_list)
        self.variables['DebitSource' + str(index)] = debit_old[ind_beg+1:ind_end+1, :]

        # Instant de début de rejet: fin du palier précédent, ou début de rejet précédent
        # si date_beg est antérieure à la première date de fin de palier
        if ind_beg != 0 or date_beg > dates[0]:
            time_beg = time_list_old[ind_beg]
        else:
            time_beg = time_begin_old
        self.variables['TimeBeginSource' + str(index)] = time_beg


    def sampleSource(self, new_dates, index=0):
        """
        Ré-échantillonne le rejet en rajoutant les dates contenues dans new_dates pour de nouveaux paliers
        La première date est le nouveau debut de rejet (correspond au TimeBeginSource)
        Les suivantes sont les fins de paliers
        (On ne change pas le TimeRef car il peut y avoir plusieurs sources dans le même fichier)
        @param new_dates: Liste de nouveaux paliers de rejet
        @type new_dates: list
        @param index: Indice de la source. Défaut: 0
        @type index: int
        """
        # Paramètres de la source
        time_list_old = self.variables['TimeSource' + str(index)]
        time_begin_old = float(self.variables['TimeBeginSource' + str(index)])
        debit_old = self.variables['DebitSource' + str(index)]

        # Liste de dates correspondant à la source
        old_dates = self.getSourceDate(index)

        # On rajoute le début du rejet
        date_ref = string_to_datetime_fr(self.variables["TimeRef"])
        old_dates.insert(0, date_ref + datetime.timedelta(seconds=time_begin_old))

        # Nouvelles dates (fusion des deux listes et élimination des doublons)
        # NB: on prend le dénominateur commun des 2 listes et non pas seulement new_dates
        dates = unique(np.array(list(old_dates) + list(new_dates)))
        Nt = len(dates)-1
        self.data['DateSource' + str(index)] = dates[1:]

        # Nouveau début de rejet, nouveaux paliers
        time_list = np.array([(d - date_ref).days * 24 * 3600 +  (d - date_ref).seconds for d in dates])
        self.variables['TimeBeginSource' + str(index)] = time_list[0]
        self.variables['TimeSource' + str(index)] = time_list[1:]
        self.dimensions['NTimeSource' + str(index)] = Nt

        # Nouveaux débits
        Niso = debit_old.shape[1]
        debit = zeros((Nt, Niso), 'd')
        for t in range(Nt):
            # Date de fin de palier
            d = dates[t+1]
            # print("Date de fin de palier", d.strftime("%d/%m/%Y %H:%M"))
            # print("Plage de rejet", old_dates[0].strftime("%d/%m/%Y %H:%M"), old_dates[-1].strftime("%d/%m/%Y %H:%M"))
            # Si on est en dehors de l'ancienne plage de rejet, on laisse les zéros
            if d > old_dates[0] and d <= old_dates[-1]:
                # Indice de fin de palier de l'ancien rejet
                ind = find_nearest_date_end(d, old_dates[1:])
                debit[t,:] = debit_old[ind,:]
        self.variables['DebitSource' + str(index)] = debit


    #####################################
    # GESTION DES ESPÈCES ET DES DÉBITS #
    #####################################

    def getSpeciesRate(self, species, index=0):
        """
        renvoie la liste des débits de rejet pour une espèce donnée
        @param index: Indice de la source. Défaut: 0
        @type index: int
        @param species: Espèce que l'on veut
        @type species: string
        @return: la liste de débits de rejet
        @rtype: list
        """

        # Paramètres de la source
        species_list = self.variables['IsoNameListSource' + str(index)]
        debit = self.variables['DebitSource' + str(index)]
        Nt = debit.shape[0]
        Niso = len(species)
        if species not in species_list:
            print("Species", species, " not in list.")
            return zeros((Nt), 'd')
        else:
            ind = species_list.index(species)
            return debit[:, ind]


    def addMltFactor(self, species, factor, index=0):
        """
        Ajout d'un facteur multiplicatif sur le debit de certaines espèces, pour la source d'indice index.
        @param species: "all" ou famille ("GR", "iode", "cesium", "non_GR") ou liste des isotopes.
        @type species: str ou list
        @param factor: facteur multiplicatif.
        @type factor: float ou list
        @param index: Indice de la source. Défaut: 0
        @type index: int
        """
        # Listes d'especes et de facteurs.
        if type(species) == str:
            if species == 'all':
                species_list = self.variables['IsoNameListSource' + str(index)]
                factor_list = [factor for i in range(len(species_list))]
            elif species.lower().rstrip('s') in ['gr', 'iode', 'cesium', 'non_gr']:
                species_list = getFamilySpecies(self.variables['IsoNameListSource' + str(index)], species)
                factor_list = [factor for i in range(len(species_list))]
        else:
            species_list = species
            factor_list = factor

        # Multiplication de debit.
        for spec, fac in zip(species_list, factor_list):
            ind = self.variables['IsoNameListSource' + str(index)].index(spec)
            self.variables['DebitSource' + str(index)][:, ind] *= fac


    def selectSpecies(self, species, index=0):
        """
        Filtre les isotopes à conserver dans le terme source, pour la source d'indice index.
        @param species: Liste des isotopes.
        @type species: list
        @param index: Indice de la source. Défaut: 0
        @type index: int
        """
        # Paramètres de la source
        species_list = self.variables['IsoNameListSource' + str(index)]
        debit = self.variables['DebitSource' + str(index)]
        Nt = debit.shape[0]
        Niso = len(species)

        # Remplissage du tableau pour les espèces que l'on garde
        debit_out = zeros((Nt, Niso), 'd')
        species_ind = []
        for i in range(Niso):
            ind = species_list.index(species[i])
            species_ind.append(self.variables['IsoIdListSource' + str(index)][ind])
            debit_out[:, i] = debit[:, ind]

        # Nouveaux paramètres
        self.variables['DebitSource' + str(index)] = debit_out
        self.variables['IsoNameListSource' + str(index)] = np.array(species)
        self.variables['IsoIdListSource' + str(index)] = np.array(species_ind)
        self.dimensions['NIsoSource' + str(index)] = Niso


    def addSpecies(self, species, species_ind, debit, index=0):
        """
        Ajoute un isotope pour la source d'indice index.
        @param species: isotope à rajouter
        @type species: string
        @param species_ind: indice de l'isotope
        @type species_ind: int
        @param debit: debit de l'isotope aux pas de temps de rejet
        @type debit: list
        @param index: Indice de la source. Défaut: 0
        @type index: int
        """
        # Paramètres de la source
        species_list = list(self.variables['IsoNameListSource' + str(index)])
        species_ind_list = list(self.variables['IsoIdListSource' + str(index)])
        Nt = self.dimensions['NTimeSource' + str(index)]

        # Vérification du nombre de pas de temps
        if len(debit) != Nt:
            print("addSpecies: la liste des débits doit avoir le bon nombre de paliers de rejet")
            print("isotope ", species, ": ", len(debit), "valeurs et ", Nt, " paliers!")
            sys.exit(1)

        # Si l'isotope existe déjà, on se contente de changer le débit
        if species in species_list:
            ind = species_list.index(species)
            self.variables['DebitSource' + str(index)][:, ind] = debit

        # Remplissage du tableau pour les nouvelles espèces
        else:
            species_list.append(species)
            species_ind_list.append(species_ind)
            Niso = len(species_list)
            debit_out = zeros((Nt, Niso), 'd')
            debit_out[:, :Niso-1] = self.variables['DebitSource' + str(index)]
            debit_out[:, -1] = debit

            # Nouveaux paramètres
            self.variables['DebitSource' + str(index)] = debit_out
            self.variables['IsoNameListSource' + str(index)] = np.array(species_list)
            self.variables['IsoIdListSource' + str(index)] = np.array(species_ind_list, 'i')
            self.dimensions['NIsoSource' + str(index)] = Niso


    def addSource(self, date_list, species_list,species_ind_list, rate_list, index=0):
        """
        Ajout d'une source dans le fichier
        """
        # Indice de la source ajoutée
        try:
            Ns = int(self.variables["NSource"])
            self.variables["NSource"] = Ns + 1
            source_index = Ns
        except KeyError:
            source_index = 0
            attr = {"long_name": "Nombre de sources",
                    "units": ""}
            self.createVariable("NSource", source_index + 1, (), attr, 'i')

        # Maillage de référence
        self.globalAttr["Source_RefPointsSet" + str(source_index)] = str(index)
        self.globalAttr["Source_long_name" + str(source_index)] = "source"

        # TimeList
        self.setDateList(date_list, False, source_index)

        # Création des variables: débit, liste d'isotopes, liste d'indices d'isotopes
        dimkey = "NIsoSource" + str(source_index)
        Niso = len(species_list)
        self.dimensions[dimkey] = Niso

        # Liste d'isotopes
        varkey = "IsoNameListSource" + str(source_index)
        attr = {"long_name": "Nom des isotopes",
                "units": ""}
        self.createVariable(varkey, np.array(species_list), (dimkey,'NMaxChar'), attr, 'c')

        # Liste d'indices
        varkey = "IsoIdListSource" + str(source_index)
        attr = {"long_name": "Indice des isotopes",
                "units": ""}
        self.createVariable(varkey, np.array(species_ind_list, dtype='i'), (dimkey,), attr, 'i')

        # Liste de débits de rejet
        varkey = "DebitSource" + str(source_index)
        timekey = "NTimeSource" + str(source_index)
        Nt = self.dimensions[timekey]
        attr = {"long_name": "Debit de rejet par isotope",
                "units": "Bq/s"}
        self.createVariable(varkey, np.array(rate_list).reshape(Nt, Niso), (timekey, dimkey), attr, 'd')


    ###############################################
    # CALCUL DU CUMUL ET AFFICHAGE CUMUL ET DEBIT #
    ###############################################


    def writeCumul(self, cumul_file = "", index=0):
        """
        @param cumul_file: fichier où les cumuls sont écrits
        @type cumul_file: string
        @param index: Indice de la source. Défaut: 0
        @type index: int
        """
        # Calcul du cumul si nécessaire
        if not 'CumulSource' + str(index) in self.data.keys():
            cumul = self.computeCumul()

        # Nom du fichier
        if cumul_file == "":
            cumul_file = "cumul_" + self.name + ".txt"
        f = open(cumul_file, "w")

        # Entête du fichier
        f.write(u"# Cumul du rejet (Bq)\n")
        dates = self.getSourceDate(index)
        f.write("# Cumul entre le " + dates[0].strftime("%d-%m-%Y %H:%M") + " et le " \
                    + dates[-1].strftime("%d-%m-%Y %H:%M"))
        f.write("\n# Nombre d'isotopes: " + str(self.dimensions['NIsoSource' + str(index)]))

        # Ecriture des cumuls (isotopes et familles)
        f.write("\n## Cumul des isotopes")
        species_list = self.variables['IsoNameListSource' + str(index)]
        Niso = len(species_list)
        for species in species_list:
            iso = list(self.variables['IsoNameListSource' + str(index)]).index(species)
            f.write("\n" + species + "\t" + "%1.2e"%float(self.data['CumulSource' + str(index)][-1, iso]))
        f.write("\n## Cumul des familles")
        for family in sort(self.data['CumulFamily' + str(index)].keys()):
            f.write("\n" + family + "\t" + "%1.2e"%float(self.data['CumulFamily' + str(index)][family][-1]))

        # Fermeture du fichier
        f.close()


    def computeCumul(self, index=0):
        """
        Calcule le cumul rejeté en fonction du temps pour tous les isotopes.
        @param index: Indice de la source. Défaut: 0
        @type index: int
        """
        # Données de source
        species_list = self.variables['IsoNameListSource' + str(index)]
        debit= self.variables['DebitSource'+str(index)]
        tsource = self.variables['TimeSource' + str(index)]
        tbeginsource = float(self.variables['TimeBeginSource' + str(index)])
        Nt = debit.shape[0]
        Niso = debit.shape[1]

        # Calcul du cumul rejeté
        cumul = zeros((Nt, Niso), 'd')
        for iso in range(Niso):
            cumul[0, iso] = debit[0, iso] * (tsource[0] - tbeginsource)
            for it in range(1, Nt):
                cumul[it, iso] =  cumul[it-1, iso] + \
                    debit[it, iso] * (tsource[it] - tsource[it-1])

        # Cumul des familles
        self.data['CumulFamily'+str(index)] = {}
        for family in ['tous_iso', 'GR', 'iodes', 'cesiums', 'non_GR']:
            species_family = getFamilySpecies(species_list, family)
            family_cumul = zeros((Nt), 'd')
            for sp in species_family:
                iso = list(self.variables['IsoNameListSource' + str(index)]).index(sp)
                family_cumul += cumul[:, iso]
            self.data['CumulFamily'+str(index)][family] = family_cumul

        self.data['CumulSource'+str(index)] = cumul
        return self.data['CumulSource'+str(index)]


    def plotRateSource(self, species, figure_path=".", date_beg=0, date_end=-1, index=0):
        """
        Trace le débit (instantané et cumulé) pour les isotopes contenus dans species ("all" pour tous).
        @param species: "all" ou famille ou isotope.
        @type species: str
        @param date_beg: Début du tracé de rejet (date ou indice dans la liste de dates).
        @type date_beg: datetime ou int
        @param date_end: Fin du tracé de rejet (date ou indice dans la liste de dates).
        @type date_end: datetime ou int
        @param figure_path: Chemin des figures (défaut: chemin courant)
        @type figure_path: string
        @param index: Indice de la source. Défaut: 0
        @type index: int
        """
        # Listes d'espèces
        sum_species = False
        if species == 'all':
            species_list = self.variables['IsoNameListSource' + str(index)]
        elif species.lower().rstrip('s') in ['gr', 'iode', 'cesium', 'non_gr', 'tous_iso']:
            species_list = getFamilySpecies(self.variables['IsoNameListSource' + str(index)], species)
            sum_species = True
            family = species.lower()
        else:
            species_list = [species]

        # Troncature des dates (pour la figure uniquement)
        dates = self.getSourceDate(index)
        ind_beg, ind_end = truncateDates(date_beg, date_end, dates)
        dates = dates[ind_beg:ind_end+1]

        # Boucle sur les isotopes
        debit = {}
        cumul = {}
        debit_tot = {self.name: zeros((len(dates)), 'd')}
        cumul_tot = {self.name: zeros((len(dates)), 'd')}
        dates_tot = {self.name: dates}
        for species in species_list:
            iso = list(self.variables['IsoNameListSource' + str(index)]).index(species)
            debit[self.name] = self.variables['DebitSource'+str(index)][ind_beg:ind_end+1, iso]
            debit_tot[self.name] += debit[self.name]

            # Calcul du cumul si nécessaire
            try:
                cumul[self.name] = self.data["CumulSource"+str(index)][ind_beg:ind_end+1, iso]
            except KeyError:
                cumul[self.name] = self.computeCumul()[ind_beg:ind_end+1, iso]
            cumul_tot[self.name] += cumul[self.name]

            # Plot des débits et des cumuls.
            if not sum_species:
                plotRateSpecies(dates_tot, debit, "debit", species, figure_path)
                plotRateSpecies(dates_tot, cumul, "cumul", species, figure_path)

        # Plot de la somme sur les espèces (pour les familles)
        if sum_species:
            plotRateSpecies(dates_tot, debit_tot, "debit", family, figure_path)
            plotRateSpecies(dates_tot, cumul_tot, "cumul", family, figure_path)


    def plotRateFamily(self, figure_path=".", date_beg=0, date_end=-1, index=0):
        """
        Trace le débit (instantané et cumulé) pour les différentes familles d'isotopes
        @param date_beg: Début du tracé de rejet (date ou indice dans la liste de dates).
        @type date_beg: datetime ou int
        @param date_end: Fin du tracé de rejet (date ou indice dans la liste de dates).
        @type date_end: datetime ou int
        @param figure_path: Chemin des figures (défaut: chemin courant)
        @type figure_path: string
        @param index: Indice de la source. Défaut: 0
        @type index: int
        """
        family_list = ['tous_iso', 'GR', 'non_GR', 'Cesiums', 'Iodes']
        for family in family_list:
            self.plotRateSource(family, figure_path, date_beg, date_end, index)


    ###################################
    # TRANSFORMATION EN FICHIER TEXTE #
    ###################################


    def writeSourceText(self, file_out, species_list=[], iodine_sum=False, index=0):
        """
        Ecrit un fichier texte avec les débits de rejet par palier pour les isotopes demandés
        @param file_out: Nom du fichier texte de sortie
        @type file_out: string
        @param species_list: Liste des isotopes à écrire (défaut: [] = tous les isotopes)
        @type species_list: string list
        @param iodine_sum: True si sommation des iodes (gaz et aerosol) (défaut: False)
        @type iodine_sum: bool
        @param index: Indice de la source. Défaut: 0
        @type index: int
        """
        if species_list == []:
            species_list = self.variables['IsoNameListSource' + str(index)]

        # Entête
        f = open(file_out, 'w')
        f.write('# Debut rejet (local): ' + self.getSourceBeginDate().strftime('%d/%m/%Y %H:%M:%S') + '\n')
        f.write("# Debit en Bq/s".ljust(16) + "\n")
        if iodine_sum:
            f.write("# Sommation des iodes\n")
        f.write("# Date_fin_palier".ljust(20))
        f.write("".join([species.ljust(16) for species in species_list]))

        # Récupération des dates et des débits pour les isotopes demandés
        dates = self.getSourceDate(index)
        Nt = len(dates)
        for it in range(Nt):
            output_str = ["\n", dates[it].strftime('%d/%m/%Y %H:%M:%S').ljust(20)]
            # Boucle sur les isos et sommation des iodes si demandé
            for species in species_list:
                if "I-" in species and iodine_sum:
                    if it == 0:
                        print("Sommation des formes d'iode (gaz+aerosol+moleculaire) pour ", species)
                    rate = self.getSpeciesRate(species.split("_")[0]).copy()
                    if species + "_I" in self.variables['IsoNameListSource' + str(index)]:
                        rate += self.getSpeciesRate(species + "_I")
                    if species + "_IM" in self.variables['IsoNameListSource' + str(index)]:
                        rate += self.getSpeciesRate(species + "_IM")
                else:
                    rate = self.getSpeciesRate(species)
                output_str.append("{0:1.4e}".format(rate[it]).ljust(16))
            f.write("".join(output_str))

        f.close()


#########################
# SOMMATION DES SOURCES #
#########################


def add_sources(sources, source_out, data_path):
    """
    Sommation des sources contenues dans la liste sources, et écriture de la somme dans source_out
    NB: seules les sources d'indice 0 sont prises en compte et sommées dans le cas de fichiers à plusieurs sources.
    Les débits des familles sont également tracés, et les cumuls écrits dans un fichier texte.
    @todo: généraliser pour des indices de sources différents de 0
    @param sources: liste des noms de fichiers .nc de sources à sommer
    @type sources: list
    @param source_out: nom de fichier .nc où écrire la source sommée
    @type source_out: string
    @param data_path: chemin des fichiers .nc
    @type data_path: string
    """
    # Recherche dates et isotopes communs à toutes les sources
    new_dates = []
    new_iso = []
    ind_dic = {}
    for source_in in sources:
        ts = Source(os.path.join(data_path, source_in))
        old_dates = ts.getSourceDate(0)

        # On rajoute le début du rejet
        time_begin_old = float(ts.variables['TimeBeginSource0'])
        date_ref = string_to_datetime_fr(ts.variables["TimeRef"])
        old_dates.insert(0, date_ref + datetime.timedelta(seconds=time_begin_old))
        new_dates += old_dates

        # Isotopes
        iso_list = ts.variables['IsoNameListSource0']
        ind_list = ts.variables['IsoIdListSource0']
        new_iso += iso_list

        # Dictionnaire d'indices correspondant aux isotopes
        for iso, ind in zip(iso_list, ind_list):
            if iso not in ind_dic.keys():
                ind_dic[iso] = ind

    # Dates et isotopes communs à toutes les sources
    new_dates = unique(np.array(new_dates))
    Nt = len(new_dates) - 1
    new_iso = unique(np.array(new_iso))
    new_ind = [ind_dic[iso] for iso in new_iso]
    Niso = len(new_iso)

    # Boucle sur les sources pour les sommer
    new_rates = zeros((Nt, Niso), 'd')
    for source_in in sources:
        print("\n#Ajout source", source_in)

        # Recupération données
        ts = Source(os.path.join(data_path, source_in))
        tsource = ts.variables["TimeSource0"]
        tbeginsource = float(ts.variables['TimeBeginSource0'])
        #print("TimeRef", ts.variables["TimeRef"])
        date_ref = string_to_datetime_fr(ts.variables["TimeRef"])
        dates = ts.getSourceDate(0)

        # Nouvel échantillonnage de dates
        ts.sampleSource(new_dates)
        dates = ts.getSourceDate(0)

        # Ajout d'isotopes si besoin
        species_list = ts.variables['IsoNameListSource0']
        species_ind_list = ts.variables['IsoIdListSource0']
        #print(new_iso, species_list)
        for ind, iso in enumerate(new_iso):
            if iso not in species_list:
                ts.addSpecies(iso, new_ind[ind], zeros((Nt),'d'))
                sp = -1
            else:
                sp = species_list.index(iso)
            # On range les débits dans le bon ordre
            new_rates[:, ind] += ts.variables["DebitSource0"][:, sp]
        ts.variables['IsoNameListSource0'] = new_iso
        ts.variables['IsoIdListSource0'] = new_ind

        # Affichage cumul pour vérification
        cumul = ts.computeCumul()
        for family in ts.data['CumulFamily0'].keys():
            print("Cumul", family, ": %1.2e"%float(ts.data['CumulFamily0'][family][-1]))

    # Sommation des sources
    print("\n# Sommation des sources", source_out)
    date_ref = new_dates[0]
    ts.variables["DebitSource0"] = new_rates
    ts.setTimeRef(date_ref)
    time_source = [(d - date_ref).days * 24 * 3600 + (d - date_ref).seconds for d in new_dates]
    ts.variables["TimeSource0"] = time_source[1:]
    ts.variables["TimeBeginSource0"] = 0
    ts.data["DateSource0"] = new_dates[1:]
    ts.dimensions["NTimeSource0"] = Nt
    ts.dimensions["NIsoSource0"] = Niso

    # Nouveau cumul
    cumul = ts.computeCumul()
    for family in ts.data['CumulFamily0'].keys():
        print("Cumul", family, ": %1.2e"%float(ts.data['CumulFamily0'][family][-1]))
    ts.name = source_out.rstrip(".nc")

    # NB: les attributs et variables non explicitement changés ici sont ceux du dernier fichier lu
    ts.globalAttr["Source_long_name0"] = ts.name
    ts.globalAttr["PointsSet_long_name0"] = ts.name
    ts.variables["NPointsSet"] = 1
    ts.variables["NSource"] = 1

    # Il ne faut pas que le dernier fichier contienne plus d'une source, sinon elles sont toutes réécrites
    for var in ts.variables.keys():
        if var[-1].isdigit() and int(var[-1]) != 0:
            del ts.variables[var]
    for var in ts.dimensions.keys():
        if var[-1].isdigit() and int(var[-1]) != 0:
            del ts.dimensions[var]

    # Ecriture source
    ts.writeNC(os.path.join(data_path, source_out))

    # Figures et fichier de cumuls
    figure_path = os.path.join(data_path, "figures_" + ts.name)
    if not os.path.isdir(figure_path):
        os.makedirs(figure_path)

    print("Figures des debits de rejet dans ", figure_path)
    cumul_file= os.path.join(figure_path, "cumul_" + ts.name + ".txt")
    ts.writeCumul(cumul_file)
    ts.plotRateFamily(figure_path)


def append_source(source_in, source_out, data_path, index_in=0):
    """
    Ajout d'une source contenue dans source_in à la suite du fichier source_out
    @param source_in: nom de fichier .nc de source à ajouter
    @type source_in: string
    @param source_out: nom de fichier .nc dans lequel la source_in sera rajoutée à la suite des autres sources
    @type source_out: string
    @param data_path: chemin des fichiers .nc
    @type data_path: string
    @param index_in: indice de la source à ajouter (défaut: 0)
    @type index_in: int
    """
    # Données fichier nc de sortie (pour connaître le TimeRef et le nombre de sources)
    file_name = os.path.join(data_path, source_out)
    ts = Source(file_name)
    TimeRef = ts.variables["TimeRef"]
    date_ref = string_to_datetime_fr(TimeRef)
    Np = int(ts.variables["NPointsSet"])
    Ns = int(ts.variables["NSource"])
    print("Nombre de sources existantes dans le fichier:", Ns)

    # Recupération données source à ajouter
    ts = Source(os.path.join(data_path, source_in))
    date_beg = ts.getSourceBeginDate(index_in)
    dates_in = ts.getSourceDate(index_in)

    # Dates par rapport au nouveau TimeRef
    time_source = [(d - date_ref).days * 24 * 3600 + (d - date_ref).seconds for d in dates_in]
    time_begin_source = (date_beg - date_ref).days * 24 * 3600 + (date_beg - date_ref).seconds
    ts.variables["TimeSource"+str(index_in)] = time_source
    ts.variables["TimeBeginSource"+str(index_in)] = time_begin_source

    # Nouveau nombre de points et nouvel indice de source
    ts.variables["NSource"] = Ns + 1
    ts.variables["NPointsSet"] = Np + 1
    index_out = Np

    # Ecriture des variables avec le nouvel indice
    ts.file = file_name
    file_out = NetCDFFile(file_name, 'a')

    # Dimensions
    for name, value in ts.dimensions.iteritems():
        name = increment(name, index_out)
        print(name)
        if name not in file_out.dimensions.keys():
            file_out.createDimension(name, value)

    # Attributs globaux
    for name, value in ts.globalAttr.iteritems():
        name = increment(name, index_out)
        if  "Source_RefPointsSet" in name:
            setattr(file_out, name, index_out)
        else:
            setattr(file_out, name, value)


    # Variables
    for var in ts.variables.keys():
            name_out = increment(var, index_out)
            print(name_out)
            dim_out = tuple([increment(dim, index_out) for dim in ts.variableDim[var]])
            print(dim_out)
            if name_out not in file_out.variables.keys():
                print(name_out, "new variable")
                var_out = file_out.createVariable(name_out, ts.variableType[var], dim_out)

                # Conversions en liste de char avec la bonne dimension (transformation inverse de concat_str)
                if var.startswith("IsoName"):
                    char_iso = [str_to_char(species, ts.dimensions['NMaxChar']) for species in ts.variables[var]]
                    var_out.assignValue(np.array(char_iso))
                else:
                    var_out.assignValue(ts.variables[var])

                # Attributs des variables
                for name, value in ts.variableAttr[var].iteritems():
                    setattr(var_out, name, value)
            elif var != "TimeRef":
                var_out = file_out.variables[var]
                var_out.assignValue(ts.variables[var])

    file_out.sync()
    file_out.close()
