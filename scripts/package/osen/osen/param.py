# -*- coding: utf-8 -*-

import configparser


def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def load_parameters(file_path):

    # Créer un objet ConfigParser
    config = configparser.ConfigParser()

    # Charger le fichier INI
    config.read(file_path)

    # Créer un dictionnaire pour stocker les paramètres
    parameters = {}

    # Parcourir les sections et les clés du fichier INI
    for section in config.sections():
        for key, value in config.items(section):
            if ',' in value:
                # Diviser la valeur en une liste de valeurs
                values = value.split(',')
                # Enlever les espaces blancs et stocker la liste dans le dictionnaire
                parameters[key] = [v.strip() for v in values]
            # Vérifier si la valeur est un nombre
            elif value.isdigit():
                parameters[key] = int(value)
            elif is_float(value):
                parameters[key] = float(value)
            else:
                parameters[key] = value

    return parameters
