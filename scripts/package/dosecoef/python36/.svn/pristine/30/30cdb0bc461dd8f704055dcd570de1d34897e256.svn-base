# -*- coding: utf-8 -*-
""" Ce module teste les fonctions du module DoseCoef """

import unittest
from numpy import array, allclose
from dosecoef.dosecoef import GlobalIsoCoef


class DoseCoefTest(unittest.TestCase):
    def testDef(self):
        """ Construction de l'objet de GlobalIsoCoef sur 3 isotopes """
        self.assertTrue(GlobalIsoCoef(["Cs-137", "I-131", "Cs-134"]))

    def testDef1(self):
        """ Appel d'un vecteur de coef, VA ne nécessitant pas de paramètre de granu ou de solubilité """
        self.assertEqual(GlobalIsoCoef(["Cs-137", "I-131", "Cs-134"]).queryCoef("adulte", "Depot"),
                         [2.8499999999999998e-019, 3.76e-016, 1.52e-015])
        self.assertEqual(GlobalIsoCoef(["Cs-137", "I-131", "Cs-134"]).queryCoef("adulte", "Panache", "1.0", "S", "Sein"),
                         [9.6700000000000002e-018, 2.04e-014, 8.4300000000000004e-014])

    def testDef2(self):
        """ Appel d'un vecteur de coef, granulo et solubilité commun et imposés pour tous les iso """
        self.assertEqual(GlobalIsoCoef(["Cs-137", "I-131", "Cs-134"]).queryCoef("adulte", "Inhalation", "1.0", "M"),
                         [9.6999999999999992e-009, 2.4e-009, 9.1000000000000004e-009])

    def testDef3(self):
        """ Appel d'un vecteur de coef, granulo et solubilité imposés par isotope """
        self.assertEqual(GlobalIsoCoef(["Cs-137", "I-131", "Cs-134"]).queryCoef("adulte", "Inhalation", ["1.0", "0.1", "0.1"], ["M", "S", "F"]),
                         [9.6999999999999992e-009, 2.6000000000000001e-009, 7.8000000000000004e-009])

    def testDef4(self):
        """ Appel d'un vecteur de coef, granulo ou solubilité imposés par isotope """
        self.assertEqual(GlobalIsoCoef(["Cs-137", "I-131", "Cs-134"]).queryCoef("adulte", "Inhalation", ["1.0", "0.1", "0.1"]),
                         [4.5999999999999998e-009, 8.7999999999999994e-009, 7.8000000000000004e-009])
        self.assertEqual(GlobalIsoCoef(["Cs-137", "I-131", "Cs-134"]).queryCoef("adulte", "Inhalation", None, ["M", "S", "F"]),
                         [9.6999999999999992e-009, 1.6000000000000001e-009, 6.6000000000000004e-009])

    def testSolubiliteV(self):
        """
        Teste la requête d'un coef de dose avec solubilité V.
        @object: Teste la requête d'un coef de dose sur le Ru avec solubilité V.
        @desc: Requête du coefficient inhalation pour la cible 1an pour l'isotope Ru-103 avec la solubilité V.
        @check: Vérifie que la valeur correspond à 6.2E-9.
        @testtype: TG
        """
        self.assertEqual(GlobalIsoCoef(["Ru-103"]).queryCoef("1an", "Inhalation", solu="V"), [6.2000000000000001e-09])

    def testExtendedFormIsotopes(self):
        """
        Teste la recherche de coefficients pour des formes chimiques évoluées de certains isotopes.
        @object: Teste les requêtes de coefficients de différentes formes de l'isotope Ru.
        @desc Requête du coefficient inhalation pour la cible adulte pour les formes
        Ru-106-Aero, Ru-106-FG1, Ru-106-Fg2 et de différents coefficients pour le Ru-106 avec différentes solubilités.
        @check: Vérifie que le coefficient d'une forme chimique correspond au coefficient du Ru-106
        avec la solubilité correspondante.
        @testtype: TU
        """
        self.assertEqual(GlobalIsoCoef(["Ru-106_FG1"]).queryCoef("adulte", "Inhalation"),
                         GlobalIsoCoef(["Ru-106"]).queryCoef("adulte", "Inhalation", solu="F"))
        self.assertEqual(GlobalIsoCoef(["Ru-106_FG2"]).queryCoef("adulte", "Inhalation"),
                         GlobalIsoCoef(["Ru-106"]).queryCoef("adulte", "Inhalation", solu="S"))


class DoseCoefTestSurBug(unittest.TestCase):
    def testDef(self):
        """
        Choix de la solubilité la plus pénalisante en cas d'incompatibilité (bug #2, #3).
        Test qui vérifie que lorsque la solubilité par défaut n'est pas compatible avec la cible choisi,
        dosecoef utilise la solubilité la plus pénalisante.
        Cas du Pb-214 avec la cible travailleur et la va inhalation. Suite à bug #2 et #3 (consx tracker).
        """
        self.assertEqual(GlobalIsoCoef(["Pb-214"]).queryCoef("travailleur", "Inhalation"), [2.8999999999999999e-09])

    def testDef1(self):
        """
        Coef. des isotopes du Mercure (bug #4)
        Vérifie que dosecoef gère correctement le cas du Mercure.
        Construction d'un objet GlobalIsoCoef() avec du mercure sous différentes formes chimiques.
        Requête des coef de doses inhalation pour 3mois, 5ans, adulte.
        """
        g = GlobalIsoCoef(["Hg-193", "Hg-195_HI", "Hg-199m_HG", "Hg-197m_HV"])
        # Liste qui contiendra les résultats
        res = []
        for cible in ["3mois", "5ans", "adulte"]:
            res.append(g.queryCoef(cible, "inhalation"))
        self.assertEqual(allclose(array(res, "f"), array([[2.2e-10, 5.3e-10, 1.4e-10, 2.01e-08],
                                                          [8.2e-11, 2.0e-10, 4.2e-11, 1.1e-8],
                                                          [2.4e-11, 7.3e-11, 1.5e-11, 5.8e-9]], "f")), True)

    def testDef2(self):
        """
        Surcharge de la granu et/ou de la solu d'un isotope abs de l'instance(Bug #24)
        Vérifie que la surcharge de la granu et/ou de la solu d'un isotope qui n'est pas dans l'objet GlobalIsoCoef()
        lève un warning mais n'entraine pas d'erreur. Suite à Bug #24.
        """
        self.assertEqual(GlobalIsoCoef(["Pb-214", "Cs-137"]).queryCoef("adulte",
                                                                       "Inhalation",
                                                                       solu={"Cs-137": "S", "U-236": "S"},
                                                                       granu={"Pb-214": "3.0", "I-131": "5.0"}),
                         [1.9000000000000001e-08, 3.8999999999999998e-08])

    def testDef3(self):
        """
        Isotopes absents d'ECRIN.
        Pour les isotopes absents d'ECRIN, notés -999 dans le fichier Coefs.pxs,
        dosecoef doit émettre un warning et retourner 0 quelle que soit la requête formulée.
        """
        self.assertEqual(GlobalIsoCoef(["Bi-204"]).queryCoef("adulte", "Depot"), [0.0])
        self.assertEqual(GlobalIsoCoef(["Tl-210"]).queryCoef("adulte", "Inhalation"), [0.0])
        self.assertEqual(GlobalIsoCoef(["Cu-57"]).queryCoef("adulte", "Panache"), [0.0])


if __name__ == '__main__':
    unittest.main()
