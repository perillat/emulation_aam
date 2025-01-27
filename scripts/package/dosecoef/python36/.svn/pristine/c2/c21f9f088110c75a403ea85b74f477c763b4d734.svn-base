# -*- coding: utf-8 -*-
"""
Script lançant une campagne de tests, qui inclut tous les modules de test du programme.
Il collecte et exécute l'ensemble des modules de test disponibles dans un répertoire donné.
"""

__revision__ = "$Id: runTests.py 1289 2009-06-16 09:34:30Z didier $"

import argparse
import os
import platform
import sys
import unittest
from pkg_resources import get_distribution, DistributionNotFound


__ADDED_PATHS = []

# Nom du package à tester (à ventiler)
PKGTEST = 'dosecoef'

# Liste des noms des modules dont le package à tester dépend.
DEPLIST = []

# Chaine de cadre
FRAME = '\n' + 40 * '*' + '\n'

# Sortie
f_out = sys.stdout


##################################################

def run_tests(root_path, exclude_dir_list):
    """
    Parcours les répertoires et exécute les scripts de test.
    Seules les répertoires commençant par 'test' sont parcourus.
    Dans chacun de ces répertoires, tous les scripts python commençant par 'test' sont exécutés.
    @param root_path: chemin à partir duquel les scripts de test sont recherchés.
    @param exclude_dir_list: liste de chemins à exclure.
    """
    def is_excluded(dir_path):
        for excluded_path in exclude_dir_list:
            if dir_path.startswith(excluded_path):
                return True
        return False

    test_modules = []

    for root, _, files in os.walk(root_path):
        dossier = os.path.basename(root)
        if dossier.startswith('test') and not is_excluded(root):
            for file in files:
                if file.startswith('test') and file.endswith('.py') and file != 'test.py':
                    test_modules.append(file)
                    if root not in sys.path:
                        sys.path.append(root)
                        old_added_path = __ADDED_PATHS
                        old_added_path.append(root)
                        globals()['__ADDED_PATHS'] = old_added_path

    module_names = list(map(lambda f: os.path.splitext(f)[0], test_modules))
    modules = list(map(__import__, module_names))
    load = unittest.defaultTestLoader.loadTestsFromModule
    test_suite = unittest.TestSuite(list(map(load, modules)))
    campagne = unittest.TextTestRunner(verbosity=2)
    campagne.run(test_suite)


def pkg_version_string():
    """
    Retourne une chaîne de caractères avec la version du package qui va être testée.
    """
    return '\nPackage testé : ' + PKGTEST + '-' + get_distribution(PKGTEST).version + '\n' + FRAME


def computer_config_string():
    """
    Fonction qui retourne une chaîne de caractères contenant les infos sur la config du pc hôte.
    """
    name = platform.node()
    arch = platform.machine()
    proc = platform.processor()
    pyt_version = sys.version
    ope_sys = platform.system()
    vers = platform.release()
    detail_vers = 'None'
    if ope_sys == 'Linux':
        try:
            detail_vers = '-'.join(platform.dist())
        except AttributeError:
            pass
    # Mise en forme
    return f'Configuration machine détectée :\n' \
           f'{FRAME}' \
           f'    Nom :          {name}\n' \
           f'    Architecture : {arch}\n' \
           f'    Processeur :   {proc}\n' \
           f'    OS :           {ope_sys}-{vers} ({detail_vers})\n' \
           f'    python         {pyt_version}\n'


def dependances_details_string():
    """
    Retourne la version de package liste en var globale (DEP) représentant les dépendances.
    (si le package n'a pas été installé avec setuptools, pas d'info).
    """
    out_str = 'Version des dépendances :\n' + FRAME
    not_founded = []
    for dep in DEPLIST:
        try:
            dist = get_distribution(dep).version
            out_str += dep + '-' + dist + '\n'
        except DistributionNotFound:
            not_founded.append(dep)
    if not_founded:
        out_str += f'Packages présents, mais versions non identifiées : {", ".join(not_founded)}\n'
    return out_str


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=f'Exécute les tests pour {PKGTEST}.')
    parser.add_argument('-r', '--repertoire', metavar='<REP>', default='.',
                        help='Spécifie le répertoire à utiliser, si non fourni, le chemin courant est utilisé')
    parser.add_argument('-m', '--module',  metavar='<MOD>',
                        help=f'Spécifie le chemin du module {PKGTEST} à utiliser, si non fourni, '
                             f'le module {PKGTEST} du site-packages est utilisé')
    parser.add_argument('-e', '--exclude-dir',  metavar='<DIRS>',
                        help='Spécifie les chemins (séparés par :) où les scripts de test ne seront pas recherchés.')
    args = parser.parse_args()

    if args.module:
        module = os.path.abspath(args.module)
        if module not in sys.path:
            sys.path.insert(0, module)
            oldAddedPath = __ADDED_PATHS
            oldAddedPath.append(module)
            globals()['__ADDED_PATHS'] = oldAddedPath
    else:
        # Écriture de la version testée
        f_out.write(pkg_version_string())

    if args.repertoire:
        path = args.repertoire
    else:
        path = os.getcwd()
    path = os.path.abspath(path)
    path = os.path.normpath(path)
    if path.endswith(os.path.sep):
        path = path[:-1]

    # Option permettant d'exclure des répertoires.
    if args.exclude_dir is not None:
        ex_dir_list = [os.path.abspath(ex_dir) for ex_dir in args.exclude_dir.split(':')]
        f_out.write(f'Les tests contenus dans les répertoires suivants ne seront pas exécutés :\n')
        for ex_dir in ex_dir_list:
            f_out.write(f'  - {ex_dir}\n')
    else:
        ex_dir_list = []

    f_out.write(computer_config_string())  # Ecriture config.
    f_out.write(dependances_details_string())  # Ecriture Version des dépendances.
    f_out.write('\nDébut des tests...\n')
    run_tests(path, ex_dir_list)
    f_out.flush()

    for path in __ADDED_PATHS:
        sys.path.remove(path)
