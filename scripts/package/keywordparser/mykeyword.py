# -*- coding: iso-8859-15 -*-
"""
@todo: docstring du module
"""
__revision__ = "$Id: keyword.py 1334 2009-11-03 11:10:48Z cayrol $"

from copy import copy
import os, io

_REQUIRE_KEY = {'Opt': False, 'Req':True}
_REQUIRE_NAME = { False : 'Opt', True : 'Req'}

#Mode d'acces aux fichiers
_ACCESS_MODE = {'r': os.R_OK, 'w':os.W_OK}
_ACCESS_NAME = { os.R_OK : 'r', os.W_OK :'w'}

#Caractere de separation
_SC = "="
#Caractere de range.
_RC = "<x<"
#Caractere de liste
_LC = "|"
#Caractere pour indexation
_IDC = '.'

class KeyWordParserError(Exception):
    """
    Classe d'exception pour le module.
    """
class NoValueError(Exception):
    """
    Classe levee quand aucune valeur n'est definie pour le mot cle.
    """
class FileAccessError(Exception):
    """
    Classe levée lorsque qu'un fichier pointé par un mot cle n'est as accessible
    avec les droits demandes.
    """
class EltOutListError(KeyWordParserError):
    """
    Exception du module KeyWordParser qui herite de la classe KeyWordParserError.

    Cette exception est levee lorsqu'une valeur donnee n'est pas dans
    la liste des possibilites.
    """

class Keys:
    '''
    Methodes publiques de la classe Keys:
        - getKeyIdList(keyName)
        - getKeyValue(keyName, id=None)
        - getKeysNames()
        - getKeysLongNames()

    @todo: description de la classe
    @param defFile: est le fichier contennant la definition des mots cle
    @param userFile: est le fichier de l'utilisateur exploitant les mots cles

    '''

    def __init__(self, defFile, userFile):
        """
        Methode d'initialisation de la classe Keys.

        @param defFile:  Nom du fichier contenant la definition des mots cles.
        @param userFile: Nom du fichier de l'utilisateur exploitant les mots
                                    cles.
        """
        # Definition de cles avec le fichier defFile.
        self.keyList = buildKeyList(defFile)
        # Liste d'ordre des cles lue dans le fichier param.
        self.keyUserList = []
        # Lecture du fichier user. Agit sur les deux listes.
        self.__upLoadUserFile(userFile)

    def __upLoadUserFile(self, userFile):
        """
        Lecture du fichier parametrique de l'utilisateur.

        Méthode qui parcours le fichier utilisateur pour charger les valeurs
        des mots cles reconnus, c'est à dire dans la liste keyList.
        Ces valeurs sont stockees dans ces clé et dupliquer lorsque les mots
        clés utilisent des indexes. Les mots clé sont référencés dans la liste
        keyuserList dans l'ordre ou ils ont été rencontrés.

        @param userFile: Chemin du fichier parametrique de l'utilisateur.
        @raise KeyWordParserError: dans tous les cas d'erreur.
        """
        if 'keyList' not in self.__dict__.keys():
            raise KeyWordParserError.with_traceback(u"Execution de upLoadUserFile necessite " \
                          u"self.keyList construit par" \
                          u"keys.__init__()")
        else:
            checkCoding(userFile)
            uFile = open(userFile, 'r')
            for line in uFile:
                if not lineIsComment(line):
                    words = splitAndStrip(line, _SC)
                    self.loadUserLine(words)
            #Fermeture du fichier utilisateur.
            uFile.close()
        #Test cle requise
        self.testRequireKey()
    def loadUserLine(self, words):
        """
        Méthode de chargement d'une ligne d'un fichier utilisateur.
        @param words: Liste consitué du nom long du mot cle et de la valeur.
        """
        isFind = False
        if len(words) < 2 :
            raise KeyWordParserError.with_traceback(u"La ligne --%s-- "\
                " n'a pas le bon separateur." % (words))
        # Identification du mots cle.
        # Teste si la ligne lue corespond à  une clée.
        for key in self.keyList:
            if words[0] == key.longName:
                isFind = True
                key.setValue(words[1])
                self.keyUserList.append(key)
        if not isFind:
            # Si le mot cle n'est pas directement trouve on etudie
            #les cas ou le mot cle est multiple.
            splitLine = splitAndStrip(words[0], _IDC)
            if len(splitLine) > 1:
                for key in self.keyList:
                    if splitLine[0] == key.longName:
                        keyId = splitLine[1:]
                        # On duplique la cle.
                        self.keyList.append(copy(key))
                        # Update du long name et id.
                        key = self.keyList[-1]
                        #Ajoute la cle dans la liste de cle def par le user.
                        self.keyUserList.append(key)
                        key.longName = words[0]
                        key.id = keyId
                        key.setValue(words[1])
                        isFind = True
                        break
        if not isFind:
            # La ligne lue n'est pas un commentaire et ne corespond
            # A aucun des mots clés.
            raise KeyWordParserError.with_traceback(u"Le mot cle - %s - du fichier" \
                                    " user est inconnu" % words[0])
        return isFind

    def testRequireKey(self):
        """
        Méthode qui test si les cles requises ont une valeur.
        @raise KeyWordParserError:Si une cle requise n'a pas de valeur.
        """
        for key in self.keyList:
            try:
                key.getValue()
            except NoValueError as msg:
                if key.isRequire:
                    raise KeyWordParserError.with_traceback("%s : La cle %s est requise" \
                                            % (msg, key.name))

    def getKeyIdList(self, keyName):
        """
        Retourne la liste des id d'une clef.

        Retourne 'None' si la clef est unique, sinon retourne la liste des id.
        @param keyName: Nom de la clef.
        @return: La liste des id de la clef, 'None' si la clef est unique.
        """
        idList = []
        for key in self.keyList:
            if key.name == keyName:
                if hasattr(key, 'id'):
                    idList.append(key.id)
                else:
                    idList.append('None')
        return idList

    def __getKey(self, keyName, kId=None, onlyUserKey=False):
        """
        Méthode privée qui retourne l'objet key.
        Si la cle n'existe pas, l'exception KeyWordParserError est levée.

        @param keyName: Nom de la cle.
        @param kId: identifiant de la cle. Utile si la cle est multiple.
        @param onlyUserKey: Si True, la recherche se limite au cles definie par
        l'utilisateur, sil false, la recherche se fait sur toutes les cles
        (fichier definition et user).
        @raise KeyWordParserError: Levee si la clef n'existe pas.
        """
        idStr = ''
        if onlyUserKey == True:
            keyList = self.keyUserList
        else:
            keyList = self.keyList
        # Recherche de la clef.
        for key in keyList:
            if key.name == keyName:
                if kId == None:
                    return key
                elif hasattr(key, 'id') and key.id == kId:
                    return key
                else:
                    idStr = '(' + str(kId) + ')'
            else:
                pass
        else:
            raise KeyWordParserError.with_traceback("La cle %s%s n'existe pas" %(keyName, idStr))

    def getKey(self, keyName, kId=None):
        """
        Fonction qui retourne l'objet key.
        Si la cle n'existe pas, l'exception KeyWordParserError est levée.

        @param keyName: Nom de la cle.
        @param kId: identifiant de la cle. Utile si la cle est multiple.
        @raise KeyWordParserError: Levee si la clef n'existe pas.
        """
        return self.__getKey(keyName, kId, onlyUserKey=False)

    def getUserKey(self, keyName, kId=None):
        """
        Fonction qui retourne l'objet key en recherchant dans le cles definies
        par l'utilisateur.
        Si la cle n'existe pas, l'exception KeyWordParserError est levée.

        @param keyName: Nom de la cle.
        @param kId: identifiant de la cle. Utile si la cle est multiple.
        @raise KeyWordParserError: Levee si la clef n'existe pas.
        """
        return self.__getKey(keyName, kId, onlyUserKey=True)

    def setKeyValue(self, keyName, value, kId=None):
        """
        Fonction qui affecte la valeur @value à la clé. Si la cle n'existe pas,
        l'exception AttributeError est levée. Cette méthode ne cree pas de cle
        (contrairement à loadUserKeyValue qui peut de fait, crée des clés indicés).
        @param keyName: Nom de la cle.
        @param value: Valeur.
        @param kId: identifiant de la cle. Utile si la cle est multiple.
        @raise KeyWordParserError: Levee si la clef n'existe pas.
        """
        self.getKey(keyName, kId).setValue(value)

    def loadUserKeyValue(self, keyName, value, kId=None):
        """
        Fonction qui ajoute un mot clé et sa valeur comme si il avait été lu dans
        fichier parametrique.
        @param keyName: Nom de la cle.
        @param value: Valeur.
        @param kId: identifiant de la cle. Utile si la cle est multiple.
        @raise KeyWordParserError: Levee si la clef n'existe pas.
        """
        k = self.getKey(keyName)
        line = k.longName
        if kId != None:
            words = [line]
            words.extend(kId)
            line = _IDC.join(words)
        self.loadUserLine([line, str(value)])

    def suppUserKey(self, keyName, kId=None):
        """
        Fonction qui supprime une clé définie par un utilisateur.

        @param keyName: Nom de la cle.
        @param kId: identifiant de la cle. Utile si la cle est multiple.
        @raise KeyWordParserError: Levee si la clef n'existe pas.
        """
        k = self.getUserKey(keyName, kId)
        self.keyUserList.remove(k)
        self.keyList.remove(k)

    def getKeyValue(self, keyName, kId=None):
        """
        Fonction qui retourne la valeur d'une clé. Si la cle n'existe pas,
        l'exception AttributeError est levée.

        @param keyName: Nom de la cle.
        @param kId: identifiant de la cle. Utile si la cle est multiple.
        @raise KeyWordParserError: Levee si la clef n'existe pas.
        """
        k = self.getKey(keyName, kId)
        return k.getValue()

    def keyValueIsSetByUser(self, keyName, kId=None):
        """
        Fonction qui retourne True si la cle a une valeur definie par le user,
        et False si il s'agit de la valeur par defaut.

        @param keyName: Nom de la cle.
        @kId: identifiant de la cle. Utile si la cle est multiple.
        @raise AttributeError: Levee si la clef n'existe pas.
        """
        # Recherche de la clef.
        for key in self.keyList:
            if key.name == keyName:
                if kId == None:
                    return key.getValue()
                elif hasattr(key, 'id') and key.id == kId:
                    return key.valueIsSetByUser()
                else:
                    pass
            else:
                pass
        else:
            raise AttributeError("La cle %s n'existe pas" %(keyName))
    def getKeysNames(self):
        """
        Fonction qui retourne une liste contenant, dans leur ordre de
        stockage, le nom des clÃ©s.
        """
        keysNames = []
        for k in self.keyList:
            keysNames.append(k.name)
        return keysNames
    def getKeysLongNames(self):
        """
        Fonction qui retourne une liste contenant, dans leur ordre
        de stockage, le nom long des clÃ©s.
        """
        keysNames = []
        for k in self.keyList:
            keysNames.append(k.longName)
        return keysNames
    def writeDefFile(self, nameDefFile):
        """
        Méthode qui ecrite le fichier de definition de mots cle
        correspondant à l'état de l'objet Keys.
        @param nameDefFile: Nom du fichier de définition à créer.
        """
        fDef = open(nameDefFile, "w")
        lines = []
        for k in self.keyList:
            line = k.getDefLine() + '\n'
            if line != '':
                lines.append(line)
        fDef.writelines(lines)
        fDef.close()
    def writeUserFile(self, nameUserFile):
        """
        Méthode qui ecrite le fichier de definition de mots cle
        correspondant Ã  l'état de l'objet Keys.
        @param nameDefFile: Nom du fichier de utilisateur à créer.
        """
        fUser = open(nameUserFile, "w")
        lines = []
        for k in self.keyUserList:
            line = k.getUserLine() + '\n'
            if line != '':
                lines.append(line)
        fUser.writelines(lines)
        fUser.close()
class Key:
    """
    Classe abstraite qui definit les methodes et attributs communs à tous les
    types de mots clés.
    """
    def __init__(self, words):
        """
        Initialise la classe Key.
        @param words: Liste de chaine de caractéres (Ligne du fichier de
        definition splitée.
        """
        # Nom de la cle
        self.name = words[0]
        # Nom long associe (utilise dans le param de l'utilisateur)
        self.longName = words[1]
        #  Mot clé necessaire.
        if words[2] in _REQUIRE_KEY.keys():
            self.isRequire = _REQUIRE_KEY[words[2]]
        else:
            raise KeyWordParserError.with_traceback(u"La clé %s doit faire partie de %s. %s lu!" \
            % (self.name, _REQUIRE_KEY.keys(), words[2]))
        #Chargement des contraintes sur la valeur du mot cle
        self._loadConstrains(words)
        #Chargement de la valeur par defaut si la cle est optionnelle.
        if self.isRequire == False:
            self.setDefValue(words[4])
    def setDefValue(self, strVal):
        """
        Affecte la valeur par defaut contennue dans la chaine
        passee en arguments.
        @param strVal: Chaine contennant la valeur.
        @return :Si la chaine vaut "None", la méthode ne fait rien.
        Si la chaine contient une valeur ne satisfaisant pas les contraintes,
        EltOutListError est levée.
        Sinon, la valeur est affectee et type à  l'attributs defValue.
        """
        if not isNone(strVal):
            self.defValue = self.type(strVal)
            self._checkConstrains(self.defValue)
    def setValue(self, strVal):
        """
        Affecte la valeur contennue dans la chaine
        passee en arguments.
        @param strVal: Chaine contennant la valeur.
        @return : Si la chaine vaut "None" ou si la chaine contient une valeur ne
        satisfaisant pas les contraintes, EltOutListError est levée.
        Sinon, la valeur est affectee et type à  l'attributs value.
        """
        if not isNone(strVal):
            self.value = self.type(strVal)
            self._checkConstrains(self.value)
        else:
            raise EltOutListError( u"La valeur None n'est pas accepte dans "
                                   u"le fichier de paramétre (Mot clé: %s)." % self.longName)
    def _checkConstrains(self, value):
        """
        Vérifie que la valeur passee en argument verfiie les contraintes
        de la cle.
        """
        if (not hasattr(self, 'listElement') and not\
            hasattr(self,'rangeValue')):
            return True
        elif 'listElement' in self.__dict__.keys() \
                       and value in self.listElement:
            return True
        elif 'rangeValue' in self.__dict__.keys() \
                       and isInRange(value, self.rangeValue):
            return True
        else:
            raise EltOutListError(u"La valeur du fichier user \
                                 - %s - n'est pas dans la \
                                 liste ou gamme definie"
                                % value)

    def _loadConstrains(self, words):
        """
        Charge les contraintes sur les valeurs possibles.
        """
        if len(words) == 6 and words[5] != None:
            # Deux configurations:: definition d'une liste de valeurs
            # possibles, ou definition d'une gamme
            # (int & float uniquement)
            elementListSize = words[5].count(_LC) + 1
            if words[5].count(_RC) == 1 and elementListSize == 1 \
               and len(splitAndStrip(words[5], _RC, self.type)) == 2:
                # Une gamme de valeur est definie pour la cle.
                self.rangeValue = splitAndStrip(words[5], _RC,
                                                        self.type)

                ## rmodif
                if (self.rangeValue[1] != None):
                    if (self.rangeValue[0] > self.rangeValue[1]):
                        raise ValueError(u"Erreur definition cle %s: " \
                                         u"La definition d'un gamme de " \
                                         u"valeur par a%sb impose que a<b"
                                         % (self.name, _RC))


            elif words[5].count(_RC) == 0 \
                  and len(splitAndStrip(words[5], _LC, \
                                self.type)) == elementListSize:
                #Une liste de possibilite est definie
                self.listElement = splitAndStrip(words[5], _LC,
                                                            self.type)
            else:
                raise KeyWordParserError.with_traceback(u"Le formatage d'une liste un d'une " \
                   u"gamme pour la cle %s n'est pas " \
                   u"respecte " % self.name)

    def getValue(self):
        """
        Retourne la valeur prise par la clé.
        """
        if hasattr(self,'value'):
            self.isGet = True
            return self.value
        elif hasattr(self, 'defValue') and not self.isRequire:
            self.isGet = True
            return self.defValue
        else:
            raise NoValueError("Pas de valeur")

    def valueIsSetByUser(self):
        """
        Methode qui premet de savoir si un mot cle utilise la valeur par
        defaut ou la valeur donne par le user.
        @return: True si la valeur est donnee par l'utilisateur et False si
                        si c'est la valeur par defaut.
        """
        return hasattr(self,'value')

    def getDefLine(self):
        """
        Méthode qui retourne la ligne déclarant le mot clé.
        Dans le cas ou le mot cle est indexé, la chaine vide est retournée
        car il n'a pas à apparaitre dans le fichier de définition du mot clé.
        @return chaine de caractere au format du fichier de definition ou chaine
        vide.
        """
        if not hasattr(self, 'id'):
            line = self.name + _SC + self.longName + _SC  \
                    + _REQUIRE_NAME[self.isRequire] + _SC \
                    + self.typeName + _SC
            if not self.isRequire:
                if hasattr(self, "defValue"):
                    line += str(self.defValue)
                else:
                    line += "None"
            line += _SC + self.getConstrainsLine()
            return line
        else:
            return ''

    def getConstrainsLine(self):
        """
        Méthode qui retourne la chaine definissant la constrainte sur
        le mot cle.
        """
        if 'listElement' in self.__dict__.keys():
            line = str(self.listElement[0])
            if len(self.listElement) > 1:
                for elt in self.listElement[1:]:
                    line += _LC + str(elt)
            return line
        elif 'rangeValue' in self.__dict__.keys():
            line = str(self.rangeValue[0]) + _RC + str(self.rangeValue[1])
            return line
        else:
            return ''

    def getUserLine(self):
        """
        Méthode qui retourne la définition du mot clé au format du fichier user.
        @return chaine de caractère au format du fichier user ou
        si le mot clé n'a pas de valeur autre que la valeur par defaut,
        la méthode retourne None.
        """
        if self.valueIsSetByUser:
            line = self.longName
            return line + _SC + str(self.value)

class KeyInt(Key):
    """
    Classe pour les mots cles de type entier.
    """
    def __init__(self, words):
        """
        Initialise la classe KeyInt.
        @param words:  Liste de chaine de caractéres (Ligne du fichier de
        definition splitée).
        """
        self.type = int
        self.typeName = 'int'
        Key.__init__(self, words)

class KeyFloat(Key):
    """
    Classe pour les mots cles de type float.
    """
    def __init__(self, words):
        """
        Initialise la classe KeyFloat.
        @param words:  Liste de chaine de caractéres (Ligne du fichier de
        definition splitée).
        """
        self.type = float
        self.typeName = 'float'
        Key.__init__(self, words)


class KeyStr(Key):
    """
    Classe pour les mots cles de type string.
    """
    def __init__(self, words):
        """
        Initialise la classe KeyStr.
        @param words:  Liste de chaine de caractéres (Ligne du fichier de
        definition splitée).
        """
        self.type = str
        self.typeName = 'str'
        Key.__init__(self, words)


class KeyFile(Key):
    """
    Classe pour les mots cles de type file.
    """
    def __init__(self, words):
        """
        Initialise la classe KeyFile.
        @param words:  Liste de chaine de caractéres (Ligne du fichier de
        definition splitée.
        """
        self.type = io.TextIOWrapper
        self.typeName = 'file'
        Key.__init__(self, words)

    def _checkConstrains(self, value):
        """
        La methode est redefinie pour le type file.
        """
        if os.access(value, self.modeFile):
            return True
        else:
            if self.modeFile == os.W_OK:
            #Si mode ecriture et que le fichier n'existe pas
            #il faut tester les droits sur la directory.
                if os.path.dirname(value) == '':
                    dirPath = '.'
                else:
                    dirPath = os.path.dirname(value)
                if os.access(dirPath, self.modeFile):
                    #Si le fichier n'existe pas et si la directory
                    #est en ecriture, c'est bon.
                    return True
            # Si le return precedent n'est pas envoye, la contrainte n'est pas
            #statisfaite.
            raise FileAccessError("Fichier %s inaccessible en mode %s" %
                    (value,_ACCESS_NAME[self.modeFile]))

    def setDefValue(self, strVal):
        """
        Affecte la valeur par defaut contennue dans la chaine
        passee en arguments.
        @param strVal: Chaine contennant la valeur.
        @return :Si la chaine vaut "None", la mÃ©thode ne fait rien.
        Si la chaine contient une valeur ne satisfaisant pas les contraintes,
        EltOutListError est levée.
        Sinon, la valeur est affectee et type Ã   l'attributs defValue.
        """
        if not isNone(strVal):
            self.defValue = strVal
            self._checkConstrains(self.defValue)

    def _loadConstrains(self, words):
        """
        Méthode redefinie pour le type file.
        Charge le mode d'accès du fichier.
        """
        if words[5]  in _ACCESS_MODE.keys():
            self.modeFile = _ACCESS_MODE[words[5]]
        else:
            raise KeyWordParserError.with_traceback("Le mode de la cle de type file %s"\
                                                "n'est pas reconnu" % self.name)
    def setValue(self, strVal):
        """
        Affecte la valeur contennue dans la chaine
        passee en arguments.
        @param strVal: Chaine contennant la valeur.
        @return : Si la chaine vaut "None" ou si la chaine contient une valeur
        ne satisfaisant pas les contraintes, EltOutListError est levée.
        Sinon, la valeur est affectee et type à  l'attributs value.
        """
        if not isNone(strVal):
            self.value = strVal
            self._checkConstrains(self.value)
        else:
            raise EltOutListError( u"La valeur None n'est pas accepte dans "/
                                                "le fichier de paramétre (Mot "\
                                                "clé: %s)." % self.longName)
    def getConstrainsLine(self):
        """
        Méthode qui retourne la chaine definissant la contrainte sur
        le mot cle.
        """
        return _ACCESS_NAME[self.modeFile]


KEY_TYPE_BUILDER = { 'int' : KeyInt,
                                'float': KeyFloat,
                                'str': KeyStr,
                                'file': KeyFile}
def buildKey(line):
    """
    Fonction qui lit une ligne de definition d'un mot clé et la renvoie
    @param line: Ligne de definition d'un mot cle qui doit etre valide.
    """
    words = splitAndStrip(line, c=_SC)
    if words[3] in KEY_TYPE_BUILDER.keys():
        return KEY_TYPE_BUILDER[words[3]](words)
    else:
        raise KeyWordParserError.with_traceback("Le type de mot cle defini dans la ligne"\
       " - %s - n'est pas reconnu." % line)

def buildKeyList(defFile):
    """
    Fonction qui lit un fichier de definition des mots clés et renvoie
    une liste de class key
    """
    fileIn = open(defFile, 'r')
    keyList = []
    for line in fileIn:
        if validLine(line):
            keyList.append(buildKey(line))
    fileIn.close()
    return keyList

def isNone(word):
    """
    Fonction qui verifie si le mot passe et None.
    @param word: mot
    @return True si le mot est "None", False sinon.
    """
    return word.lower() == "none"

def isInRange(value, pRange):
    """
    Retourne True si @Value est dans la gamme de valeur
    definie par @pRange.
    """
    if all((isinstance(value, (int, float, str)), isinstance(pRange, list),
           len(pRange) == 2,  type(pRange[0]) in [float, int, str, type(None)],
           type(pRange[1]) in [float, int, str, type(None)])):
        if pRange[0] != None and pRange[1] != None:
            return(value >= pRange[0] and value <= pRange[1])
        elif pRange[0] == None and pRange[1] != None:
            return(value <= pRange[1])
        elif pRange[0] != None and pRange[1] == None:
            return(value >= pRange[0])
        else:
            raise KeyWordParserError.with_traceback(u"isInRange:: Arguments incorrectes, " \
                                    u"range == [None,None]")
    else:
        raise KeyWordParserError.with_traceback(u"isInRange:: Arguments incorrectes %s, " \
                                    u"%s" %(type(value),type(pRange[1])))

def lineIsComment(line):
    """
    Cette fonction verifie que la ligne n'est pas un commentaire.
    """
    return any((line.strip().startswith('#'), line.strip().startswith('/'),
                len(line.strip()) < 2))

def validLine(line):
    """
    Cette fonction verifie que la ligne est valide:: pas un commentaire,
    nombre de separateur ': ' correcte
    """
    if lineIsComment(line):
        #La ligne est un commentaire
        return False
    elif line.count(_SC) not in [4, 5]:
        raise AttributeError("Format de Line incomptabilte:: %s" % line)
    else:
        return True

def splitAndStrip(line, c=None, castType=type(str())):
    """
        Cette fonction retourne une liste de type casType issue de la
        separation Line par le str c.
        Chaque element est alors depourvu des espace en debut et en fin
        de string.
    >>> a=splitAndStrip(' Bonjour: a tout le monde: 2 ',':')
    >>> print(a)
    ['Bonjour', 'a tout le monde', '2']
    """
    words = line.split(c)
    for i in range(len(words)):
        if words[i].strip() == '':
            words[i] = None
        else:
            words[i] = castType(words[i].strip())
    return words

def checkCoding(fileName):
    """
    Vérifie la possbilite de convertir les chaines du descripteur de fichier
    en unicode avec l'encodage par defaut.
    @param fileName: Descripteur de fichier.
    @todo: lorsque l'encodage sera precise dans le fichier cette fonction
    ne sera plus utile car open() devra etre remplacé
    par codecs.open(xx, encoding=ENCODE) qui retourne de l'unicode.
    """
    with open(fileName, 'r') as f:
        try:
            for i, line in enumerate(f.readlines()):
                if "#" not in line:
                    str(line)
        except UnicodeDecodeError:
            raise KeyWordParserError.with_traceback(u"La ligne %s du fichier  contient des caracteres non supportes."% (i+1))#, str(fileName)))
    return True

if __name__ == '__main__':
##    SC = _SC
##    String ='Var1' + SC + 'Je suis la 1nd variable' + SC + 'Opt' + SC + \
##        'float' + SC + '3.32' + SC + '-12<x<-3.2'
##    String ='Var1' + SC + 'Je suis la 1nd variable' + SC + 'Opt' + SC + \
##        'str' + SC + 'titi' + SC + 'tutu|toto|tata'
##    buildKey(String)
    checkCoding('../../test/testDefFileBadCoding.txt')
