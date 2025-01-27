# -*- coding: utf-8 -*-
"""
Ce module a pour objectif de tester la base de coef.
- compatibilité d'un fichiers de type Ref.pxs(form de base "id nomIso") avec le Coef.pxs utilise par dosecoef.
- identification des configurations sans r
"""

import os
import sys
import unittest
from copy import copy
from dosecoef.dosecoef import GlobalIsoCoef
from dosecoef.dosecoeferror import DoseCoefError
import logging
import types

# Fichier type Ref.pxs de reference.
# FILEREF = os.path.join(os.getenv('PX_HOME'), 'dataFile', 'Ref.pxs')
FILEREF = './Ref.pxs'


def initLogging(levelConsol=logging.INFO, fileName='test.log', levelFile=logging.INFO, errFile='err.log'):
    """ Initialisation du systeme de log. """
    # Initialisation
    logger = logging.getLogger('')
    logger.setLevel(logging.DEBUG)
    # Création d'un handler pour l'affichage console.
    console_handler = Consol()
    console_handler.setLevel(levelConsol)
    # Création d'un handler pour l'écriture dans un fichier.
    file_handler = logging.FileHandler(fileName, 'a+', encoding=sys.stdout.encoding)
    file_handler.setLevel(levelFile)
    # Création d'un handler pour les warning/erreurs
    err_file_handler = logging.FileHandler(errFile, 'a+')
    err_file_handler.setLevel(logging.WARNING)
    # Création d'un format
    formatter = logging.Formatter('%(asctime)s\t%(levelname)s\t%(name)s\t%(message)s')
    # Ajout du format aux 2 handler
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    err_file_handler.setFormatter(formatter)
    # Ajout des handler aux logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.addHandler(err_file_handler)
    # Liste des handler
    return logger


def closeLogging(log=logging.getLogger('')):
    """
    Ferme les handlers ouverts par dosecoef.
    @param log: Logger.
    """
    log.info("Fermeture du système de log.")
    # Traitement du file handler
    hlist = copy(log.handlers)
    for handler in hlist:
        if isinstance(handler, logging.FileHandler):
            handler.flush()
            handler.close()
        log.removeHandler(handler)
    logging.shutdown()


def readIsoRefPxs(file_ref):
    # Lecture du fichier ref.pxs
    with open(file_ref, 'r') as f:
        # Constructions d'une liste d'iso
        iso_list = []
        for line in f:
            try:
                iso_list.append(line.split()[1])
            except IndexError:
                pass
    return iso_list


class Consol(logging.StreamHandler):
    def emit(self, record):
        """
        Emit a record.
        La méthode est modifiée pour supporter les accents dans la term.
        """
        try:
            msg = self.format(record)
            fs = '%s\n'
            if not hasattr(types, 'UnicodeType'):  # if no unicode support...
                self.stream.write(fs % msg)
            else:
                try:
                    self.stream.write(fs % msg)
                except UnicodeError:
                    self.stream.write(fs % msg.encode('iso-8859-15'))
            self.flush()
        except:
            self.handleError(record)


class BDCoefTest(unittest.TestCase):
    """ Classe qui teste la bd de coef """

    def setUp(self):
        """ Méthode d'initilisation d'une fonction test """
        print("Fichier de ref utilisé : %s" % FILEREF)
        self.isoList = readIsoRefPxs(FILEREF)

    def test_coefInhalation(self):
        """
        Appel systématique du constructeur GlobalIsoCoef avec chacun des isotopes.
        Requête CD inhalation pour le travailleur
        Le test envisageable serait une comparaison des log...
        """
        iso_wrong_name = []
        err_file = 'errtest_coeffInhalation.log'
        logger = initLogging(errFile=err_file)
        logger.debug(2 * (100 * '*' + '\n') + 'CIBLE TRAVAILLEUR')
        for iso in self.isoList:
            try:
                print("Test %s ..." % iso)
                g = GlobalIsoCoef([iso], logger=logger)
                g.queryCoef('travailleur', 'Inhalation')
                print(" Ok")
            except DoseCoefError as e:
                if iso != 'Scalar':
                    logger.error("Erreur avec l'isotope %s - %s" % (iso, e))
                    iso_wrong_name.append(iso)
                else:
                    print("Scalar non traité...")
                    pass
        closeLogging()
        return iso_wrong_name


#     def test_coefInhalation(self):
#         """
#         Appel systématique du constructeur GlobalIsoCoef avec chacun des isotopes.
#         Requête CD Depot pour les différentes cibles.
#         Le test envisageable serait une comparaison des log...
#         """
#         isoWrongName = []
#         errFile = "errtest_coeffInhalation.log"
#         logger = initLogging(errFile=errFile)
#         for iso in self.isoList:
#             try:
#                 print "Test %s ..." % iso
#                 g = GlobalIsoCoef([iso], logger=logger )
#                 g.queryCoef("travailleur", "Inhalation")
#                 print(" Ok")
#             except DoseCoefError:
#                 if iso != "Scalar":
#                     print "Erreur avec l'isotope %s" % iso
#                     isoWrongName.append(iso)
#                 else:
#                     print("Scalar non traité...")
#                     pass
#         closeLogging()
#         return isoWrongName


def main(fileRef):
    print("Test compatibilite Ref.pxs - dosecoef ")
    print("Fichier de ref utilise: %s" % fileRef)
    print("Lecture du fichier ref...")
    iso_list = readIsoRefPxs(fileRef)
    print("Lecture Ok")
    print("Demarrage du test...")
    iso_wrong_name = test_dosecoef(iso_list)
    print("WrongName", iso_wrong_name)
    print("Test Ok")


if __name__ == '__main__':
    #   main(sys.argv[1])
    unittest.main()
