# -*- coding: iso-8859-15 -*-
"""
Ecrit un fichier de param.
"""

__revision__ = "$Id$"

import os
from keywordparser import mykeyword

mykeyword._SC = ':'

class ParamGlobal:
    def __init__(self):
        """
        Construction du gestionnaire de mots-clefs à partir du fichier template.
        """
        defParam = os.path.join(os.path.dirname(__file__), "def_template_param" )
        paramTemplate = os.path.join(os.path.dirname(__file__), "paramTemplate")
        self.keys = mykeyword.Keys(defParam, paramTemplate)

    def setDateDeb(self, dateD):
        """
        @param dateD: date sous la forme "jj/mm/aaaa HH:MM"
        """
        dayD, timeD = dateD.split(" ")
        day, month, year = dayD.split("/")
        hour, minute = timeD.split(":")
        self.keys.setKeyValue("DateDebD", day)
        self.keys.setKeyValue("DateDebM", month)
        self.keys.setKeyValue("DateDebY", year)
        self.keys.setKeyValue("DateDebH", hour)
        self.keys.setKeyValue("DateDebMi", minute)

    def setDateFin(self, dateF):
        """
        @param dateF: date sous la forme "jj/mm/aaaa HH:MM"
        """
        dayF, timeF = dateF.split(" ")
        day, month, year = dayF.split("/")
        hour, minute = timeF.split(":")
        self.keys.setKeyValue("DateFinD", day)
        self.keys.setKeyValue("DateFinM", month)
        self.keys.setKeyValue("DateFinY", year)
        self.keys.setKeyValue("DateFinH", hour)
        self.keys.setKeyValue("DateFinMi", minute)

    def setDispType(self, dispType):
        self.keys.setKeyValue("DispType", dispType)

    def loadNbEvent(self, nbEvent):
        self.keys.loadUserKeyValue("NbEvent", nbevent)

    def loadFormuleGauss(self, formuleGauss):
        self.keys.loadUserKeyValue("FormuleGauss", formuleGauss)

    def loadSeuilGauss(self, seuilGauss):
        self.keys.loadUserKeyValue("SeuilGauss", seuilGauss)

    def TauxReconstr(self, tauxReconstr):
        self.keys.loadUserKeyValue("TauxReconstr", tauxReconstr)

    def loadSigType(self, sigType):
        self.keys.loadUserKeyValue("SigType", sigType)

    def loadFactBat(self, factBat):
        self.keys.loadUserKeyValue("FactBat", factBat)

    def loadCoeffDiffH(self, coeffDiffH):
        self.keys.loadUserKeyValue("CoeffDiffH", coeffDiffH)

    def loadCoeffDiffV(self, coeffDiffV):
        self.keys.loadUserKeyValue("CoeffDiffV", coeffDiffV)

    def loadPasDeTempsADR(self, pasDeTempsADR):
        self.keys.loadUserKeyValue("PasDeTempsADR", pasDeTempsADR)

    def loadCoefPasDeTempsApPuff(self, coefPasDeTempsApPuff):
        self.keys.loadUserKeyValue("CoefPasDeTempsApPuff", coefPasDeTempsApPuff)

    def loadCoefPasDeTempsFilPuff(self, coefPasDeTempsFilPuff):
        self.keys.loadUserKeyValue("CoefPasDeTempsFilPuff", coefPasDeTempsFilPuff)

    def loadCoefPasDeTempsDepot(self, coefPasDeTempsDepot):
        self.keys.loadUserKeyValue("CoefPasDeTempsDepot", coefPasDeTempsDepot)

    def loadCoefPasDeTempsInteg(self, coefPasDeTempsInteg):
        self.keys.loadUserKeyValue("CoefPasDeTempsInteg", coefPasDeTempsInteg)

    def CoefPasDeTempsReconstr(self, coefPasDeTempsReconstr):
        self.keys.loadUserKeyValue("CoefPasDeTempsReconstr", coefPasDeTempsReconstr)

    def setMeteoFile(self, meteoFile):
        self.keys.setKeyValue("MeteoFile", meteoFile)

    def setSourceFile(self, sourceFile):
        self.keys.setKeyValue("SourceFile", sourceFile)

    def setResultFile(self, resultFile):
        self.keys.setKeyValue("ResultFile", resultFile)

    def setResultFileOut(self, resultFileOut):
        self.keys.setKeyValue("ResultFileOut", resultFileOut)

    def loadRadioElementFile(self, radioElementFile):
        self.keys.loadUserKeyValue("RadioElementFile", radioElementFile)

    def loadFamillesFile(self, famillesFile):
        self.keys.loadUserKeyValue("FamillesFile", famillesFile)

    def writeParamFile(self, paramFile):
        if not os.path.exists(os.path.dirname(paramFile)):
            os.mkdir(os.path.dirname(paramFile))
        self.keys.writeUserFile(paramFile)
