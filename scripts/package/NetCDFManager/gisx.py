# -*- coding: iso-8859-15 -*-

"""
Module d'utilitaires SIG

1 - Projection (L2E, L93, GEO) <=> (L2E, L93, GEO)
2 - Traduit les lat/long exprimées en DMS en Degrés décimaux (Fromat type: 12°32'21.2E)
3 - Calcule l'angle de convergence des méridiens.
4 - Retourne les coordonnées de points en r/theta par rapport à un point de référence.

GEO => WGS84
L2E => Lambert 2 etendu (NTF).
L93 => Lambert 93 (RGF 93)


Exemples :

1 - Projection (L2E, L93, WGS84) <=> (L2E, L93, WGS84)
-------------------------------------------------------

projX(coords,  projOrig, projDest)

Transforme coords dans le système de projection projDest.
>>> #Définit une liste de 2 point en lat/long (pts[0]=>long, pts[1]=>lat).
>>> pts = [[u"2°12'09.45O",u"1°52'40.32O"],[u"49°42'49.80N",u"49°40'37.74N"]]
>>> #Projection des coordonnées en L2E
>>> ptsL2e = projX(pts, "GEO","L2E")
>>> print(ptsL2e)
array([[  272426.54301878,   295621.00836143],
       [ 2533578.69187954,  2528194.34635608]])
>>> #Conversion de pstl2E en L93
>>> ptsL93 = projX(ptsl2e, "L2E","L93")
>>> print(ptsL93)
array([[  324818.57682147,   347955.32846084],
       [ 6969565.21217003,  6963995.4954375 ]])

2 - Traduit les lat/long exprimées en DMS en Degrés décimaux (Fromat type: 12°32'21.2E)
-------------------------------------------------------------------------------------
dmsToDec(pts)

Fonction appelée par projX si nécessaire (cf 1 )
>>> #Définit une liste de 2 point en lat/long (pt[0]=>long, pt[1]=>lat).
>>> pts = [u"2°12'09.45O",u"1°52'40.32O"],[u"49°42'49.80N",u"49°40'37.74N"]
>>> ptsDD = dmsToDec(pts)
>>> print(ptsDD)
 [-2.2026249999999998, -1.8778666666666668, 49.713833333333334, 49.677149999999997]

3 - Calcule l'angle de convergence des meridiens
----------------------------------------------
giveConvAngle(xRef, yRef, projection):

Fournit l'angle de convergence à partir des coordonnées et du système
de proj (L2E/L93).
>>> #Définit un point en L2E
>>> x, y = [-2.2026249999999998, 49.713833333333334]
>>> ca =  giveConvAngle(x, y, "L2E")
>>> print(ca)
-4.4167913404665819

4 - Retourne les coordonnées de points en r/theta par rapport à un point de référence
----------------------------------------------------------------------------------
coordsToRTheta(coords, projection, coordsRef,  projectionRef):

Cette fonction tient implicitement compte de la convergence de méridiens.
>>> # Définition d'une liste de 2 points en L2E
>>> pts = np.array([[  272426.54301878,   295621.00836143], \
            [ 2533578.69187954,  2528194.34635608]])
>>> # Définition d'un point de référence (2km plus à l'est du premier point) en L93
>>> ref =  projX([274426.54301878, 2533578.69187954],"L2E" ,"L93")
>>> # Calcul de coordonnées en r/theta par rapport au point noté ref.
>>> r, theta = coordsToRTheta(pts,"L2E",ref, "L93")
>>> print(r, theta)
array([  1997.60268185,  21841.85612794]), array([ 86.69008658, -78.81355829])

"""

from pyproj import  Proj,  transform,  Geod
import numpy as np
import re
import math
from copy import copy

#Dictionnaire définissant les pramètres des projections
_PROJ = {"GEO": "epsg:4326",
         "L2E": "epsg:27582 +es=0.0068034876 +rf=293.4660212940",#27572 L2 pas E
         "L93":"epsg:2154"}

class ProjxError(Exception):
    """Toutes les erreurs de projx sont transmises sous cette exception."""
    pass

def flatten(seq):
    """ Transforme une liste multi dimension en un une liste 1D"""
    if isinstance(seq, np.ndarray):
        return np.ravel(seq)
    if (isinstance(seq, (tuple, list))):
        #Init de la variable de sortie
        res = []
    else:
        return None
    for item in seq:
        if (isinstance(item, (tuple, list))):
            res += flatten(item)
        else:
            res.append(item)
    return res

def giveProjection(projection):
    """
    Renvoie la projection sous la forme epsg:xxxx.
    @param projection : chaine de caractères indiquant soit un code epsg : "epsg:xxx"
    soit une clé du dictionnaire _PROJ (L2E,L93, etc)
    """
    if projection in _PROJ.keys():
        return _PROJ[projection]
    elif projection.startswith("epsg"):
       return projection
    else:
        raise ProjxError("Sytème de projection %s inconnu. %s supportés." %(projection, _PROJ.keys()))

def giveConvAngle(xRef, yRef, projection):
    """
    Retourne l'angle de convergence des méridiens au point de coordonnées xRef yRef.
    @type xRef: réel
    @param xRef: Coordonnées en X.
    @type yRef: réel
    @param yRef: Coordonnées en Y.
    @type projection: string soit "L93" soit "L2E".
    @param projection:  Système des coordonnées.
    @rtype: réel
    @return: Angle en dégré de convergence des méridiens.
    """
    p = Proj(init=giveProjection(projection))

   #Projection geo
    pGeo = Proj(init=_PROJ["GEO"])


    #Projection des coordonnées de ref en geo
    xRefGeo, yRefGeo = transform(p, pGeo, xRef, yRef)

    #Deplacement sur meridien nord.
    g = Geod(ellps="WGS84")
    yGeoDelat1 =  yRefGeo + .25
    (t1,t2, dist) = g.inv(xRefGeo,yRefGeo, xRefGeo, yGeoDelat1)
    xRefDelta1, yRefDelta1 = transform(pGeo, p, xRefGeo, yGeoDelat1)
    yGeoDelat2 =  yRefGeo - .25
    (t1,t2, dist2) = g.inv(xRefGeo,yRefGeo, xRefGeo, yGeoDelat2)
    xRefDelta2, yRefDelta2 = transform(pGeo, p, xRefGeo, yGeoDelat2)

    #Calcul de l'angle
    tetha1 = math.degrees(math.asin((xRef-xRefDelta1)/dist))
    tetha2 = math.degrees(math.asin((xRefDelta2-xRef)/dist2))

    return (tetha2+tetha1)/2.

def dmsToDec(coordsList):
    """
    Transforme les lat/long en dégrés decimaux.
    Format d'entrée <xx°xx'xx.xx{N,S, E,O}> exemple "12°32'21.2E"
    @param coordsList: Liste de coordonnées exprimées en degrées/minutes seconde.
                                à transformer
    @return: liste des mêmes coordonées exprimées en degrés décimaux.
    """
    coordsDec = []
    for coord in coordsList:
        try:
            data = re.search("(?P<deg>[\d]+)°(?P<min>[\d]+)'(?P<sec>[\d.]+)(?P<card>[NSEO])", coord).groupdict()
        except AttributeError:
            print(u"""%s n'est pas au format attendu ex: 2°12'21.2N"""%coord)
        else:
            card = data["card"]
            if card in ["O","S"]:
                deg = -float(data["deg"])
                minDec =  -float(data["min"])/60. - float(data["sec"])/3600.
            else :
                deg = float(data["deg"])
                minDec =  float(data["min"])/60. + float(data["sec"])/3600.
            coordsDec.append(deg+minDec)

    return coordsDec

def translateGeoCoords(coords):
    """
    Traduit les coordonnées Geo fournies en une matrice de réels (array).
    @param coords: Conteneur des coordonnées.
                            Peut être un tuple, une liste, une matrice.
                            Peut contennir les coordonnées en dégrés décimaux, ou en DMS.
                            Seule contrainte:
                            coords[0]=> fourni les coordonnées sur x,
                            coords[1]=> fourni les coordonnées sur y.

    """
    if not isinstance(coords, np.ndarray):
        npCoords = np.array(coords)
    else:
        npCoords = copy(coords)
    origShape = npCoords.shape
    #Test que la première dim est bien de 2
    if npCoords.shape[0] != 2:
        raise ProjxError(u"La matrice à projeter n'a pas les bonnes dimension (Première dimension ==2)")
    if issubclass(npCoords.dtype.type, (np.str,  np.unicode)) :
        npCoords = np.reshape(np.array(dmsToDec(np.ravel(npCoords))), origShape)

    return npCoords

def projX(coords,  projOrig, projDest):
    """
    Réalise la projection des coordonnées @coords dans le système @projDest.
    @param coords: Matrice/liste dont la première dimesion est égale à 2.
                        (coords[0]=x, coords[1]=y) contenant les coordonnées
                        dans le système de projection défini par @projOrig.
                        Si @projOrig est GEO, les coordonnées peuvent être passées
                        en degrés décimaux ou en DMS suivant le format :
                        <xx°xx'xx.xx{N,S, E,O}> exemple "12°32'21.2E"
    @param projOrig: Système de projection de @coords au choix L2E (Lambert 2 etendu),
                            L93 (Lambert 93) ou GEO (WGS84, qui n'est pas une projection...)
    @param projDest: Système de projection  de sortie.au choix L2E (Lambert 2 etendu),
                            L93 (Lambert 93) ou GEO (WGS84, qui n'est pas une projection...)
    """
    pOrig = Proj(init=giveProjection(projOrig))
    pDest = Proj(init=giveProjection(projDest))
    if projOrig == "GEO" or projOrig == _PROJ["GEO"]:
        #Les coordonnées sont traduites dans une matrice de réels numpy .
        npCoords = translateGeoCoords(coords)
    else:
        npCoords=np.array(coords)
    #Projection des coordonnées de ref
    return np.array(transform(pOrig, pDest, npCoords[0],  npCoords[1]))

def coordsToRTheta(coords, projection, coordsRef,  projectionRef):
    """
    Retourne les coordonnées @coords exprimées en distance azimuth par
    rapport à coordsRef.
    @param coords:
    @param projection:
    @param coordsRef:
    @param projectionRef:
    """
    #Teste si coordsRef contient 2 coordonnées:
    if len(coordsRef) != 2:
        raise ProjxError("La transformation en distance/azimuth nécessite"\
                         "un point de référence défini par 2 coordonnées")
    #Transforme les coordonnées en GEO
    npCoordsRef = projX(coordsRef,  projectionRef,  "GEO")
    npCoords = projX(coords,  projection,  "GEO")
    #Mise en cohérence des shape car pour Geod il faut autant de dim au vecteur
    # de points de ref qu'au vecteur de points à projeter.
    if len(npCoords.shape) > 1 and len(npCoords.shape) <3: #Plus d'un point de défini.
        #Recupère le nombre de points
        npts = npCoords.shape[1]
        newCoordsRef = np.zeros((2, npts))
        newCoordsRef[0, :] = npCoordsRef[0]
        newCoordsRef[1, :] = npCoordsRef[1]
        npCoordsRef = newCoordsRef

    #Deplacement sur meridien nord.
    g = Geod(ellps="WGS84")
    t1,t2, dist = g.inv(npCoordsRef[0],npCoordsRef[1], npCoords[0], npCoords[1])
    return dist,  t2


if __name__ == "__main__":
    pass

#    pt = [[u"2°12'09.45O",  u"2°12'09.45O"],[u"49°42'49.80N",u"49°42'49.80N"]]
#    ref=[[u"1°52'40.32O", u"1°52'40.32O"],[u"49°40'37.74N",u"49°40'37.74N"]]
#    coordsToRTheta(ref,"GEO",pt,"GEO")
#
#    projection = "L2E"
#
#    dicPoint = {"PointEmission": ("1°52'40.32O","49°40'37.74N"),
#                    "Aurigny": ("2°12'09.45O",  "49°42'49.80N" )}
#    dicPointProj = {}
#
#    for point in dicPoint:
##        dicPoint[point] = dmsToDec(dicPoint[point])
##        print(point,  dicPoint[point])
#        dicPointProj[point] = projX(dicPoint[point],  "GEO",  projection)
#
#    print("Projection: %s"%projection)
#    for point in dicPointProj:
#        print(point,  ": %.2f\t%.2f" % (dicPointProj[point][0], dicPointProj[point][1]))


    # Valeur calculées par circé en L2E
    #pointEmission : 295621.008, 2528194.346
    #point de calcul du CTA : île d'Aurigny :  272426.543, 2533578.692


## Cas de test pour les utm
##Point en UTM30N - epsg 32630
#coords = [660791,5460104]

##Traduit en Geo :
#projX([660791, 5460104], "epsg:32630", "GEO")
##Vérifié sous circe : array([ -0.78950932,  49.27253509])

##Angle de convergence :
#giveConvAngle(660791, 5460104, "epsg:32630")
## Non vérifier : 1.6753712082144872
