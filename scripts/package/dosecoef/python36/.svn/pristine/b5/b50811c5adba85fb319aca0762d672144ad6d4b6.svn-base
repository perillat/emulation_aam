# -*- coding: utf-8 -*-
"""
Ce module donne accès à une classe qui permet d'accéder aux différents coefficients de doses contenus dans un fichier
(format a respecter).

Exemples d'utilisation :
Recherche de coef de dose inhalation pour l'adulte en imposant pour tous les isotopes une granulo et une solubilité :
>>> TS1 = GlobalIsoCoef(['Cs-137', 'I-131'])
>>> VectCoef1 = TS1.queryCoef('adulte', 'Inhalation', '1.0', 'M', 'Efficace')
>>> print(VectCoef1)
[9.6999999999999992e-009, 2.4e-009]

Avec Trois isotopes et en n'imposant pas de valeur pour les paramètres de solubilité et granulométrie :
>>> TS2 = GlobalIsoCoef(['Cs-137', 'I-131', 'Cs-134'])
>>> VectCoef2 = TS2.queryCoef('3mois', 'Inhalation')
>>> print(VectCoef2)
[8.7999999999999994e-009, 7.1999999999999996e-008, 1.0999999999999999e-008]
"""
__revision__ = "$Id: dosecoef.py 1617 2016-06-13 11:47:33Z aalbert $"

import logging
import os
import re
import sys
from .dosecoeferror import DoseCoefError, SoluFileError, CoefFileError, IsoNotFoundError, QueryError

# Chemin fichier de définition des mots clés.

# Cas du run à partir d'une installation par setup.py.
_COEF_FILE_NAME = os.path.join(os.path.dirname(__file__), 'data', 'CoefPX.pxs')
_SOLU_FILE_NAME = os.path.join(os.path.dirname(__file__), 'data', 'correspondance.pxs')

if not os.access(_COEF_FILE_NAME, os.F_OK) and not os.access(_SOLU_FILE_NAME, os.F_OK):
    # Cas du run à partir de la distribution d'un executable (pyInstaller).
    _COEF_FILE_NAME = os.path.join(os.path.dirname(sys.executable), 'data', 'CoefPX.pxs')
    _SOLU_FILE_NAME = os.path.join(os.path.dirname(sys.executable), 'data', 'correspondance.pxs')

# Expression régulière pour identifier les gaz rares
_RE_GR = re.compile(r'^(?:He|Ne|Ar|Kr|Xe|Rn)')


class GlobalIsoCoef:
    """
    Classe fournissant les coefficients de dose.
    """

    def __init__(self, isoListName, pcFileCoef=_COEF_FILE_NAME, pcFileSolu=_SOLU_FILE_NAME, logger=logging.getLogger()):
        """
        Constructeur de la classe, il nécessite une liste de nom d'isotopes.
        Le nom du fichier contenant les coefficients de doses et le nom du
        fichier contenant les solubilités peuvent être fournis optionnellement.

        @param isoListName: Liste de noms d'isotopes ex: ['Cs-137', 'Ba-135'].
        @param pcFileCoef: Directory complète du fichier de coefficient de dose.
        @param pcFileSolu: Directory complète du fichier de solubilités par défaut.
        @param logger: Objet logger qui par défaut est le logger root.
        """
        # Initialisation du logger
        logger = logging.getLogger(logger.name + '.DoseCoef')
        self.logger = logger
        logger.info("Création d'une base de coef.")
        # Construction du dictionnaire des types
        self.dataDic = giveDataDic(pcFileCoef)
        # Construction d'un dictionnaire avec comme clé l'isotope
        # et comme valeur la liste de lignes correspondant à cet isotope.
        self.dicDose = dicDoseBuild(pcFileCoef)
        # dictionnaire pour les solu
        self.dicSolu = dicSoluBuild(pcFileSolu)
        # On garde la liste qui a servi à construire l'objet car le retour de requête renvoie un vecteur de coef
        # qui respecte l'ordre de cette liste
        self.isoListName = lListCopy(isoListName)
        # Initialisation du Dictionnaire d'isotopes
        # Pour gagner du temps on classe les isotopes par ordre alpha
        # Copie de la chaine de caractères
        iso_name_sort = lListCopy(isoListName)
        logger.debug("Les isotopes sont :\n %s" % str(iso_name_sort))
        # Classement de la chaine
        iso_name_sort.sort()
        # Parcours du fichier en construisant les dictionnaires de coef pour chacun des isotopes
        # Cette fonction retourne un dictionnaire d'objet Iso
        try:
            self.dicIso = dicIsoBuild(iso_name_sort, self.dataDic, self.dicDose, self.dicSolu)
            self.nIso = len(self.dicIso)
        except Exception as e:
            raise DoseCoefError(e)

    def queryCoef(self, cible, va, granu=None, solu=None, org='Efficace'):
        """
        Retourne un vecteur de coefficients de dose.
        Si granu et solu ne sont pas donnés, les valeurs par défaut sont prises
        Si l'argument @va prend la valeur "Depot" ou "Panache", les arguments @cible, @granu , @solu seront redéfinis.

        @param cible: Choix de la cible.
        @param va: Voie d'atteinte.
        @param granu: Granulométrie (=None par défaut).
        @param solu: solubilité (=None par défaut).
        @param org: organe (="Efficace" par défaut).
        @return: Vecteur de coefficient de dose.
        """
        logger = self.logger
        # Forçage en lower case des paramètres si != none.
        if not isinstance(cible, type(None)):
            cible = cible.lower()
        if not isinstance(va, type(None)):
            va = va.lower()
        if not isinstance(org, type(None)):
            org = org.lower()
        # Nombre d'isotopes.
        n_iso = self.nIso
        try:
            # Vérifie que granu et solu sont de dimension nIso ou juste un element (F ou M ou etc)
            # ou un dico associant une solubilté/granu à un ou plusieurs isotopes.
            # La fonction retourne une liste de dim n_iso avec la valeur pour chaque éléments.
            granu = listCheckOrBuild(granu, n_iso, self.isoListName, self.logger)
            solu = listCheckOrBuild(solu, n_iso, self.isoListName, self.logger)
        except TypeError as msg:
            msg = "Erreur queryCoef : Les listes de granulométrie ou de solubilité doivent être cohérentes avec le " \
                  "nombre d'isotopes :\n%s" % msg
            self.logger.error(msg)
            raise DoseCoefError(msg)
        # Il faut traiter les cas particuliers : va = depot/panache, où granu solu doivent être forcées à 0
        if va in ('depot', 'panache'):
            cible = 'adulte'
            granu = listCheckOrBuild('none', n_iso)
            solu = granu
        # Boucle sur la liste d'isotopes utilisée a la construction de l'objet
        vect = []
        msg = '\n'
        for count, iso in enumerate(self.isoListName):
            (conf, coef) = self.dicIso[iso].queryCoef(cible, va, granu[count], solu[count], org, logger)
            vect.append(coef)
            msg += '%s - %s - %s - %s - %s - %s\n' % (conf[0], conf[1], conf[2], conf[3], conf[4], coef)
        logger.info("Coef. utilisés : " + msg)
        return vect


class Iso:
    """
    Class Iso ne devrait pas être utilisée directement mais uniquement au travers de la class GlobalIsoCoef.
    """

    def __init__(self, isoName, doseDic, soluDic, dataDic):
        """
        Constructeur de la classe Iso. Elle utilise deux fichiers pour mettre en mémoire tous les coef de doses et
        les solubilités par défaut concernant l'isotope @IsoName. Si cet isotope n'est pas présent dans
        les dictionnaires, cette méthode recherche un isotope correspondant dans le dictionnaire soluDic
        @param isoName: Nom de l'isotope (nom doit être strictement conforme aux fichiers de données).
        @param doseDic: Dictionnaire de coef de dose.
        @param soluDic: Dictionnaire indiquant les solubilités par défaut et les solubilités dispo.
        @param dataDic: Liste de dictionnaires établissant les correspondances
                                "id"=nom pour dans l'ordre la cible, la va, la granu, la solu, l'organe.
        @param dataDic: Dictionnaire de correspondances entre différentes formes chimiques des isotopes.
        """
        self.isoName = isoName
        self.isGR = isGazRare(isoName)
        self.dataDic = dataDic
        # Parcours du fichier pour trouver les lignes concernant l'iso
        self.dicCoef = {}
        try:
            if isoName not in doseDic and isoName in soluDic:
                isoName = soluDic[isoName][0][2]
            if doseDic[isoName] is None:
                self.isInEcrin = False
            else:
                self.isInEcrin = True
                for line in doseDic[isoName]:
                    # La dernière clé du dictionnaire de coef est l'organe/eff
                    dicOrgane = {'efficace': float(line[6])}
                    # Etablissement des clés temporaires
                    kCible = dataDic[0][line[2]]
                    kVa = dataDic[1][line[3]]
                    kGranu = dataDic[2][line[4]]
                    kSolu = dataDic[3][line[5]]
                    # Boucle sur les organes
                    iNOrg = len(dataDic[4])
                    for i in range(1, iNOrg + 1):
                        dicOrgane[dataDic[4][str(i)]] = float(line[6 + i])
                    if kCible in self.dicCoef.keys():
                        # Si la clé existe déjà il faut ajouter des éléments à un sous dictionnaire
                        if kVa in self.dicCoef[kCible].keys():
                            if kGranu in self.dicCoef[kCible][kVa].keys():
                                if kSolu in self.dicCoef[kCible][kVa][kGranu].keys():
                                    msg = "La combinaison a déjà été rencontrée ! Fichier de coef corrompu ?"
                                    raise CoefFileError(msg)
                                else:
                                    self.dicCoef[kCible][kVa][kGranu][kSolu] = dicOrgane
                            else:
                                self.dicCoef[kCible][kVa][kGranu] = {kSolu: dicOrgane}
                        else:
                            self.dicCoef[kCible][kVa] = {kGranu: {kSolu: dicOrgane}}
                    else:
                        # La clé n'existe pas, toute la chaine doit être créée
                        self.dicCoef[kCible] = {kVa: {kGranu: {kSolu: dicOrgane}}}
                    # Lecture de la ligne suivante
        except KeyError as details:
            raise IsoNotFoundError("L'isotope %s n'a pas été trouvé." % details)
        # Affectation solubilité et granulométrie
        self.__setDefParam(soluDic, isoBaseName=self.isoName)

    def __setDefParam(self, soluDic, isoBaseName=None):
        """
        Affecte la solubilité par défaut à l'isotope.
        @param soluDic: Dictionnaire dont les clés correspondent aux noms des isotopes et les valeurs aux lignes lues.
        """
        if isoBaseName is None:
            isoBaseName = self.isoName
        try:
            for words in soluDic[isoBaseName]:  # Boucle for inutile !!?
                # Il faut que les None
                if words[3].lower() in ['f', 'm', 's', 'none']:
                    if words[3].lower() == 'none':
                        self.defSolu = words[3].lower()
                    self.defSolu = words[3]
                else:
                    raise SoluFileError("Isotope %s : ['F', 'M', 'S', 'none'] attendu '%s' lu."
                                        % (self.isoName, words[3]))
                expected_iso = ['5.0', '10.0', 'none', '1.0', '0.1', '0.03', '0.3', '0.01', '3.0', '0.003', '0.001']
                if words[7].lower() in expected_iso:
                    self.defGranu = words[7].lower()
                else:
                    raise SoluFileError(f"Isotope {self.isoName} :\n{expected_iso} attendu, '{words[7]}' lu.")
        except KeyError as details:
            msg = "L'isotope %s n'a pas été trouvé dans le fichier de solubilité." % details
            raise IsoNotFoundError(msg)

    def queryCoef(self, cible, va, granu=None, solu=None, org='efficace', logger=logging.getLogger()):
        """
        Retourne un coef correspondant à la requête constituée des arguments de la fonction.

        @param cible: Choix de la cible.
        @param va: Voie d'atteinte.
        @param granu: Granulométrie (=None par défaut).
        @param solu: Solubilité (=None par défaut).
        @param org: Organe (='efficace' par défaut).
        @return: Vecteur de coefficient de dose.
        @todo: le mécanisme de vérification d'existence de la combinaison pourrait se baser sur les possibilités
        effectives pour l'iso et non sur les possibilités globales (dataDic).
        @todo: Le traitement pour les cas particulier où la solubilité par défaut n'est pas compatible
        avec la cible demandée, nécessite des traitements lourds.
        Une indexation différente des coef (solu en dernière clé) faciliterait le traitement.
        @param logger: Objet logger qui par défaut est le logger root.
        """
        # Booléen utilisé dans le cas où la solu par défaut n'existerait pas dans la configuration choisie
        # (notamment la cible ex pb-214 cible travailleur.)
        def_solu_is_not_valid = False
        # Vérification que les arguments prennent des valeurs possibles.
        # Valide la requête par rapport au vocabulaire utilisé dans le module.
        if cible not in self.dataDic[0].values():
            msg = "La cible %s n'existe pas. Les possibilités sont : " % cible + str(self.dataDic[0].values())
            logger.error(msg)
            raise KeyError(msg)

        if va not in self.dataDic[1].values():
            msg = "La VA %s n'existe pas. Les possibilités sont : " % va + str(self.dataDic[1].values())
            logger.error(msg)
            raise KeyError(msg)

        if granu is not None and granu not in self.dataDic[2].values():
            msg = "La granu %s n'existe pas. Les possibilités sont : " % granu + str(self.dataDic[2].values())
            logger.error(msg)
            raise KeyError(msg)

        if solu is not None and solu not in self.dataDic[3].values():
            msg = "La solubilité %s n'existe pas. Les possibilités sont : " % solu + str(self.dataDic[3].values())
            logger.error(msg)
            raise KeyError(msg)

        if org not in (list(self.dataDic[4].values()) + ['efficace']):
            msg = "L'organe %s n'existe pas. Les possibilités sont : %s" \
                  % (org, str(self.dataDic[4].values() + ['efficace']))
            logger.error(msg)
            raise KeyError(msg)
        # Si la granu n'est pas définie par l'utilisateur, on utilise la valeur par défaut sauf s'il s'agit
        # d'une solu type V qui induit implicitement un granu à 'none'.
        if granu is None and solu == 'V':
            granu = 'none'
        elif granu is None and solu != 'V':
            granu = self.defGranu

        # Si la granu n'est pas définie par l'utilisateur, on utilise la valeur par défaut.
        if solu is None:
            solu = self.defSolu
        # Série de conditions permettant de vérifier que les clés existent dans le bd de coef de l'isotope.
        # Vérification que l'iso est défini dans Ecrin
        if self.isInEcrin is False:
            msg = "L'isotope %s n'a pas de coef de dose définis (abs Ecrin)." % self.isoName
            logger.warning(msg)
            config = (self.isoName, cible, va, granu, solu, org)
            return config, 0.
        if not (cible in self.dicCoef.keys()):
            # La cible n'existe pas dans la bd, or elle a été validée au niveau de GlobalIsoCoef.
            msg = "La cible %s n'existe pas pour l'isotope %s." % (cible, self.isoName)
            logger.warning(msg)
            if cible == 'travailleur' and 'adulte' in self.dicCoef.keys():
                msg = "La cible adulte est utilisée à la place."
                logger.warning(msg)
                cible = 'adulte'
            else:
                # La cible n'existe pas, et il n'y a pas de schéma de contournement, retour 0.
                config = (self.isoName, cible, va, granu, solu, org)
                return config, 0.
        if not (va in self.dicCoef[cible].keys()):
            # La va n'existe pas.
            # Ce cas est courant et n'est pas forcément une erreur (le GR n'ont pas de va=inhalation!!)
            if not self.isGR:
                # S'il ne s'agit pas d'un GR, warning.
                logger.warning("%s n'a pas de va=%s, 0. retournée" % (self.isoName, va))
            config = (self.isoName, cible, va, granu, solu, org)
            # Valeur 0 utilisée.
            return config, 0.
        if not (granu in self.dicCoef[cible][va].keys()):
            # Si la granu n'existe pas, on utilise la valeur par défaut.
            logger.warning("La granulométrie %s n'existe pas pour %s dans la configuration. Cible::%s VA::%s."
                           " %s utilisée." % (granu, self.isoName, cible, va, self.defGranu))
            granu = self.defGranu
        if not (solu in self.dicCoef[cible][va][granu].keys()):
            # Si la solu n'existe pas, on utilise la valeur par défaut.
            asked_solu = solu
            solu = self.defSolu
            if solu in self.dicCoef[cible][va][granu].keys():
                logger.warning("La solubilité %s n'existe pas pour %s dans la configuration. Cible::%s VA::%s"
                               " granu::%s. %s utilisée (solubilité par défaut)."
                               % (asked_solu, self.isoName, cible, va, granu, self.defSolu))
            # Dans de rares cas, la solubilité par défaut n'existe pas pour certaines cibles, d'ou les tests ci-dessous.
            else:
                # Si elle n'existe pas, on prend une clé disponible et on positionne un indicateur à True
                # qui impliquera la recherche de la solubilité pénalisante.
                def_solu_key = list(self.dicCoef[cible][va][granu].keys())[0]
                # self.dicCoef[cible][va][granu][def_solu_key]
                solu = def_solu_key
                def_solu_is_not_valid = True
        else:
            asked_solu = 'none'
        if not (org in self.dicCoef[cible][va][granu][solu].keys()):
            # L'organe n'existe pas dans la bd, or il a été validé au niveau de GlobalIsoCoef.
            msg = "L'organe %s n'existe pas pour l'isotope %s (Situation anormale, fichier corrompu ?)." \
                  % (org, self.isoName)
            logger.critical(msg)
            raise QueryError(msg)
        # A ce niveau les problèmes liés à la requête sont résolus
        if def_solu_is_not_valid:
            # Recherche de la solubilité la plus pénalisante.
            solu = getSoluMaxCD(self.dicCoef[cible][va][granu], org)
            if asked_solu == 'none':
                logger.warning("L'isotope %s n'a pas de solubilité par défaut. "
                               "La solubilité pénalisante est utilisée : %s" % (self.isoName, solu))
            else:
                logger.warning("La solubilité %s n'existe pas pour %s dans la configuration. Cible::%s VA::%s"
                               " granu::%s. La solubilité la plus pénalisante est utilisée : %s"
                               " (Solubilité par défaut %s n'existe pas dans ce cas !)"
                               % (asked_solu, self.isoName, cible, va, granu, solu, self.defSolu))

        config = (self.isoName, cible, va, granu, solu, org)
        return config, self.dicCoef[cible][va][granu][solu][org]


def isGazRare(iso_name):
    """
    Retourne True si iso_name est un gaz rare
    @param iso_name: Nom de l'isotope.
    @return : True/False.
    """
    is_gr = False
    if _RE_GR.match(iso_name):
        is_gr = True
    return is_gr


def getSoluMaxCD(dicCoefGranuLevel, organe):
    """
    Fonction très spécifique destinée à retourner la solubilité la plus défavorable.
    N'est utilisée que lorsque la solubilité par défaut n'existe pas pour une certaine config (notamment cible).
    @param dicCoefGranuLevel: Extraction d'un dictionnaire type Iso.dicCoef au niveau granu
    (sa premiere clé est la solubilité).
    @param organe: Organe cible.
    """
    solu_key = dicCoefGranuLevel.keys()
    coef_list = [dicCoefGranuLevel[solu][organe] for solu in solu_key]
    return list(solu_key)[coef_list.index(max(coef_list))]


def giveDataDic(pcFileCoef):
    """
    Retourne une liste de dico indexant les différents éléments de choix d'un coef de dose utilisés dans
    le tableau des coef. Par exemple pour les cibles '1' == ' adulte'.
    @param pcFileCoef: Nom du fichier de coef de doses.
    """
    # Construction d'une chaine de caractères de key_string
    # L'ordre de la key_string doit correspondre à l'ordre dans lequel les données seront lues (ordre des colonnes).
    # Cible VA Granu Solub Organe
    key_string = ['//Cibles\n', '//VA\n', '//Granulometrie\n', '//Solubilite\n', '//Organes\n']
    liste_dico = []
    for key in key_string:
        # Boucle à la recherche de chacune des clés.
        liste_dico.append(giveDicKeyString(pcFileCoef, key))
    return liste_dico


def giveDicKeyString(pcNameFile, keyString):
    """
    Parse un fichier à la recherche de la ligne constituée uniquement de @KeyString et parse des couples "key": "value"
    pour constituer un dictionnaire.
    @param pcNameFile: Nom du fichier à parser.
    @param keyString: Chaine de caractères marquant le début de la zone à utiliser pour construire le dico.
    """
    with open(pcNameFile, 'r') as pfi:
        dico = {}
        line = pfi.readline()
        while line != keyString and line:
            # Recherche de la chaine de la ligne keystring
            line = pfi.readline()
        # Si la ligne n'est pas à keyString , la clé n'a pas été trouvée
        if line != keyString:
            raise CoefFileError("La clé %s n'a pas été trouvée." % keyString)
        # La ligne suivant keystring donne le nombre de couples à parser.
        iN = int(pfi.readline())
        for i in range(0, iN):
            # Boucle sur le nombre de couples
            line = pfi.readline()
            buff = line.split()
            # Affectation des items du dictionnaire.
            dico[buff[0]] = buff[2]
    return dico


def dicIsoBuild(isoNameSort, dataDic, doseDic, soluDic):
    """
    Fonction qui retourne un dictionnaire d'objet Iso

    @param isoNameSort: Liste des noms d'isotopes triées par ordre alpha.
    @param dataDic: Dictionnaire des types.
    @param doseDic: Dictionnaire des coef de dose par isotope.
    @param soluDic: Dictionnaire de solubilités par défaut.
    """
    dic_iso = {}
    # Boucle sur les noms des isotopes
    for isoName in isoNameSort:
        dic_iso[isoName] = Iso(isoName, doseDic, soluDic, dataDic)
    return dic_iso


def listCheckOrBuild(supposedList, sizeNeed, isoList=None, logger=logging.getLogger()):
    """
    @todo: docstring
    """
    if isinstance(supposedList, dict):
        if isinstance(isoList, list):
            tmp_list = [None] * sizeNeed
            for iso in supposedList:
                if iso in isoList:
                    tmp_list[isoList.index(iso)] = supposedList[iso]
                else:
                    logger.warning("Le choix %s=%s ne peut être appliqué, "
                                   "%s n'est pas présent dans les résultats de dispersion"
                                   % (iso, supposedList[iso], iso))
            return tmp_list
        else:
            raise (TypeError, "listCheckOrBuild:: Une liste est nécessaire lorsqu'on passe un dictionnaire")
    elif not isinstance(supposedList, list):
        # Expand value
        return [supposedList] * sizeNeed
    elif len(supposedList) != sizeNeed:
        raise (TypeError, "listCheckOrBuild:: La liste n'a pas la taille requise")
    else:
        return supposedList


def dicDoseBuild(pcFileCoef):
    """
    Construit un dictionnaire avec comme clé le nom des isotopes et comme valeur
    une liste de lignes du fichier de coef de dose qui lui sont rattachées.
    """
    dic_dose = {}
    with open(pcFileCoef, 'r') as pfi:
        for line in pfi:
            line = line.split()
            if len(line) > 3 and line[0].isdigit():
                # Si la clef n'existe pas on l'ajoute
                if not (line[1] in dic_dose.keys()):
                    dic_dose[line[1]] = []
                # On ajoute la ligne
                dic_dose[line[1]].append(line)
            elif len(line) is 3 and line[-1] == '-999':
                # L'isotope est connu mais pas dans ecrin
                dic_dose[line[1]] = None
    return dic_dose


def dicSoluBuild(pcFileCoef):
    """
    Construit un dictionnaire avec comme clé le nom des isotopes et comme valeur
    une liste de lignes du fichier de solubilité qui lui sont rattachées.
    """
    dic_solu = {}
    try:
        pfi = open(pcFileCoef, 'r')
    except IOError as details:
        details = '%s %s' % (details, pcFileCoef)
        raise IOError(details)
    for line in pfi:
        line = split_and_strip(line)
        if line[0].isdigit():
            # Si la clef n'existe pas, alors on l'ajoute
            if not (line[1] in dic_solu.keys()):
                dic_solu[line[1]] = []
            # On ajoute la ligne
            dic_solu[line[1]].append(line)
    pfi.close()
    return dic_solu


# -------------------------------------------------------------------------
# En dessous on met les fonctions les plus génériques (module maison ??)
# -------------------------------------------------------------------------

def lListCopy(src_list):
    """
    Realise un copie physique d'une liste 1D
    @param src_list : Non de la liste à copier.
    """
    new_list = [i for i in src_list]
    # for i in to_copy_list:
    #     new_list.append(i)
    return new_list


def split_and_strip(line, c=None, cast_type=str):
    """
    Cette fonction retourne une liste de type casType issue de la séparation line par le str c.
    Chaque élément est alors dépourvu des espaces en début et en fin de string.
    >>> a = split_and_strip(' Bonjour : a tout le monde : 2 ', ':')
    >>> print(a)
    ['Bonjour', 'a tout le monde', '2']
    """
    words = line.split(c)
    for i in range(len(words)):
        words[i] = cast_type(words[i].strip())
    return words


if __name__ == '__main__':
    # import doctest
    # doctest.testmod(sys.modules[__name__])
    LOGGER = logging.getLogger()
    LOGGER.setLevel(logging.DEBUG)
    # Création d'un handler pour l'affichage console.
    CONS_HANDLER = logging.StreamHandler()
    CONS_HANDLER.setLevel(logging.DEBUG)
    LOGGER.addHandler(CONS_HANDLER)
    TS2 = GlobalIsoCoef(['Ir-190l'])
    TS1 = GlobalIsoCoef(['Br-83', 'Kr-83m', 'Br-84', 'Cs-134', 'Cs-134m', 'Cs-136', 'Cs-137', 'Ba-137m', 'Cs-138',
                         'I-128', 'I-129', 'I-130', 'I-131', 'Xe-131m', 'I-132', 'I-132m', 'I-133', 'Xe-133', 'Xe-133m',
                         'I-134', 'I-135', 'Xe-135', 'Cs-135', 'Xe-135m', 'Kr-85', 'Kr-85m', 'Kr-87', 'Rb-87', 'Kr-88',
                         'Rb-88', 'Rb-89', 'Sr-89', 'Sb-125', 'Te-125m', 'Sb-127', 'Te-127', 'Te-127m', 'Sb-128m',
                         'Sb-128', 'Sb-129', 'Te-129', 'Te-129m', 'Sb-130', 'Sb-131', 'Te-131', 'Te-131m', 'Te-132',
                         'Te-133', 'Te-133m', 'Te-134', 'Xe-138', 'I-129_IM', 'I-134_IM', 'I-135_IM', 'I-133_IM',
                         'I-128_IM', 'I-131_IM', 'I-130_IM', 'I-132m_IM', 'I-132_IM'])
    TS3 = GlobalIsoCoef(['Ru-106', 'Ru-106_FG1', 'Ru-106_FG2'])
    TS4 = GlobalIsoCoef(['Ru-106'])
    VECT_COEF = TS1.queryCoef('adulte', 'Inhalation', '1.0', org='Efficace')
    VECT_COEF = TS4.queryCoef('adulte', 'Inhalation', '1.0', solu='F', org='Efficace')
    VECT_COEF = TS3.queryCoef('adulte', 'Inhalation', '1.0', org='Efficace')

    logging.shutdown()
    # dataDic = giveDataDic('CoefPX.pxs')
    # ba137m = Iso('Ba-137m', 'CoefPX.pxs', 'SolubDefault.pxs', dataDic)
