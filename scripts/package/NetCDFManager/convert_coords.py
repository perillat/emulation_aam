# -*- coding: iso-8859-15 -*-

import math
import numpy as np
from pyproj import Proj, transform, Geod
from gisx import coordsToRTheta

def get_conv_angle(lon, lat, zone='54'):
    #UTM
    p1 = Proj('+proj=utm +zone=' + zone + '+ellps=WGS84')
    #WGS84
    p2 = Proj(init = 'epsg:4326')
    g = Geod(ellps="WGS84")
    #Réalisation transfo
    x, y = transform(p2, p1, lon, lat)
    x2, y2 = transform(p2, p1, lon, lat+0.25)
    (t1,t2, dist) = g.inv(lon,lat, lon, lat+0.25)
    angle1 = degrees(asin((x-x2) / dist))
    x2, y2 = transform(p2, p1, lon, lat-0.25)
    (t1,t2, dist) = g.inv(lon,lat, lon, lat+0.25)
    angle2 = degrees(asin((x2-x) / dist))
    return (angle1 + angle2) / 2.

def convert_latlon_to_cartesian(lon, lat, lonRef, latRef, zone='54'):
     #UTM
    p1 = Proj('+proj=utm +zone=' +zone + '+ellps=WGS84')
    #WGS84
    p2 = Proj(init = 'epsg:4326')
    #Réalisation transfo
    xg, yg = transform(p2, p1, lon, lat)
    x_orig, y_orig = transform(p2, p1, lonRef, latRef)
    xg -= x_orig
    yg -= y_orig
    return xg, yg


def convert_latlon_to_rtheta(lon, lat, lonRef, latRef, trigo = True):
    # Point à convertir
    coords = np.zeros(2)
    coords[0] = lon
    coords[1] = lat
    # Point de référence
    coordsRef = np.zeros(2)
    coordsRef[0] = lonRef
    coordsRef[1] = latRef
    # Conversion to (r,theta)
    projection = "GEO"
    projectionRef = "GEO"
    r, theta = coordsToRTheta(coordsRef, "GEO", coords, "GEO")
    # Conversion en angle trigonométrique !!
    theta2 = 90. - theta
    if trigo:
        theta = theta2
    return r, theta


epsg_dic = {"GEO": "epsg:4326",
            "L93": "epsg:2154",
            "ETRS/ETRS-LAEA": "epsg:3035"}

# code EPSG.
def getEPSG(lon, lat):
    """
    Renvoie le code epsg correspondant a la projection UTM du point.
    @type lon: float
    @param lon: longitude.
    @type lat: float
    @param lat: latitude.
    @rtype: string
    @return: code epsg.
    """

    # Longitude comprise entre [-180.00; 179.9].
    lon = (lon + 180) - int((lon + 180) / 360) * 360 - 180

    zone = int((lon + 180) / 6) + 1

    if lat >= 56.0 and lat < 64.0 and lon >= 3.0 and lon < 12.0:
        zone = 32

    # Svalbard.
    if lat >= 72.0 and lat < 84.0:
        if  lon >= 0.0  and lon <  9.0:
            zone = 31
        elif lon >= 9.0  and lon < 21.0:
            zone = 33
        elif lon >= 21.0 and lon < 33.0:
            zone = 35
        elif lon >= 33.0 and lon < 42.0:
            zone = 37

    # Hémisphère nord.
    if lat >= 0:
        return "epsg:326" + str(zone)
    # Hémisphère sud.
    else:
        return "epsg:327" + str(zone)


def convert_proj_to_latlon(CoordX, CoordY, lonRef, latRef, proj):
    CoordX=np.array(CoordX)
    CoordY=np.array(CoordY)
    # Initial projection
    if proj in epsg_dic.keys():
        p1 = Proj(init = epsg_dic[proj])
        # UTM asuming there is only one zone
    else:
        # epsg = getEPSG(CoordX.mean(), CoordY.mean())
        epsg = getEPSG(lonRef, latRef)
        p1 = Proj(epsg)

    #WGS84
    p2 = Proj(init = epsg_dic["GEO"])
    #Réalisation transfo
    x_orig, y_orig = transform(p2, p1, lonRef, latRef)
    CoordX = CoordX + x_orig
    CoordY = CoordY + y_orig
    nplon, nplat = transform(p1, p2, CoordX, CoordY)
    return nplon, nplat


def convert_latlon_to_proj(lon, lat, lonRef, latRef, proj):
    # Initial projection
    if proj in epsg_dic.keys():
        p1 = Proj(init = epsg_dic[proj])
        # UTM asuming there is only one zone
    else:
        epsg = getEPSG(lonRef, latRef)
        p1 = Proj(epsg)

    #WGS84
    p2 = Proj(init = epsg_dic["GEO"])
    #Réalisation transfo
    xg, yg = transform(p2, p1, lon, lat)
    x_orig, y_orig = transform(p2, p1, lonRef, latRef)
    xg -= x_orig
    yg -= y_orig
    return xg, yg
