# -*- coding: utf-8 -*-
"""
Module qui définit les classes d'excéption de DoseCoef.
"""
__revision__ = "$Id: dosecoeferror.py 1617 2016-06-13 11:47:33Z aalbert $"


class DoseCoefError(Exception):
    """ 
    Classe d'exception principale du module DoseCoef.
    C'est cette classe qui doit être traitée (except) par les modules important le module DoseCoef
    """
    pass


class CoefFileError(DoseCoefError):
    """ Correspond à une anomalie sur le fichier de coefficients de dose """
    pass


class SoluFileError(DoseCoefError):
    """ Correspond à une anomalie sur le fichier de solubilité/granulométrie """
    pass


class IsoNotFoundError(DoseCoefError):
    """ Un isotope demandé n'est pas trouvé """
    pass


class QueryError(DoseCoefError):
    """ Erreur dans une requête """
    pass
