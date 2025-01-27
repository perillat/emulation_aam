# -*- coding: utf-8 -*-
import os, sys
import osen
import time
import numpy as np
import openturns as ot
import pickle
import matplotlib.pyplot as plt
import pandas as pd
from scipy.spatial import Voronoi, voronoi_plot_2d
from shapely.geometry import Polygon, box
import matplotlib

## Script pour créer des émulateurs à partir de simulations
## lancées précédement.

def emulateur1(krigeage, classification, scaler, dosetype, stability, FB, threshold, variable, inputs):

    inputs_normalized = scaler.transform(np.array([list(inputs)]))

    filtered  = classification[dosetype][stability][FB][threshold][variable].predict(
       inputs_normalized)[0]

    if filtered == 0:
        return 0.
    if filtered == 2:
        return 360.

    output = krigeage[dosetype][stability][FB][threshold][variable](inputs)[0]

    if variable == 'distance':
        return max(0., output)
    else:
        return 360 if (output > 180) else max(0, output)


def emulateur2(krigeage, aam, scaler, dosetype, stability, shape, inputs):

    inputs_normalized = scaler.transform(np.array([list(inputs)]))
    score_predicted = [krigeage[dosetype][stability][ii](inputs)[0] for ii in range(9)]
    prediction_flat = aam[dosetype][stability].combine(score_predicted)[0]
    prediction = prediction_flat.reshape(shape)
    return prediction, score_predicted


def format_file_path(file_path, total_length=80):
    prefix = "Reading file : "
    if len(prefix + file_path) > total_length:
        over_by = len(prefix + file_path) - total_length + 3  # +3 pour "...".
        file_path = "..." + file_path[-(len(file_path) - over_by):]
    return prefix + file_path


def read_simulations(sim_path, dosetype="Efficace", amplitude=None, lenght=None):
    """
    Lit les fichiers de simulation à partir de plusieurs chemins de fichiers
    donnés et retourne une concaténation des résultats.

    Args:
        sim_path (str or list of str): Chemin(s) vers le(s) répertoire(s)
        contenant les fichiers de simulation.
        dosetype (str, optional): Type de dose à lire, par défaut "Efficace".
        amplitude (list, optional): Amplitude du terme source à utiliser
        avec les données.

    Returns:
        np.ndarray: Tableau NumPy 3D contenant les résultats de toutes les
        simulations.

    Raises:
        ValueError: Si sim_path n'est pas une chaîne de caractères ni une
        liste de chaînes de caractères.

    """
    ## Vérification du format de result_type
    if type(sim_path) == str:
        paths = [sim_path]
    elif type(sim_path) == list:
        paths = sim_path
    else:
        print("Error: sim_path must be a string or a list of string")


    ## Initialisation du dictionnaire
    simulations = {}

    ## Boucle sur les répertoires
    for ipath, path in enumerate(paths):

        lenght_ = lenght

        first_pass = True
        dir_list = os.listdir(path)
        n_dataset = len(dir_list)

        ## On prend l'amplitude correspondante
        if amplitude == None:
            ampli = 100. * np.ones(n_dataset)
        else:
            ampli = amplitude[ipath]

        if lenght_ == None:
            lenght_ = n_dataset

        ## Boucle sur les simulations du repertoire
        for idir, dirname in enumerate(sorted(dir_list)[:lenght_]):

            ## On lit le fichier
            file_path = os.path.join(path, dirname, "Dose_"+dosetype+".npy")
            #print(format_file_path(file_path))
            dose = np.load(file_path)

            ## On initie la valeur du tableau
            if first_pass:
                shape = dose.shape
                simulations[path] = np.zeros((ampli.shape[1] * lenght_, shape[1], shape[2]))
                first_pass = False

            ## On extrait la valeur au dernier pas de temps
            for copy in range(ampli.shape[1]):
                simulations[path][copy * lenght_ + idir,:,:] = \
                    dose[-1, :, :] * ampli[idir,copy]/100.

    # On concatène tous les résultats venant de chemin différents
    return np.concatenate(list(simulations.values()), axis=0)


def pair_plot(doe, output, names=None, path=None):

    # Convertissons le tableau numpy en DataFrame pour une meilleure gestion des colonnes
    if names==None:
        df = pd.DataFrame(doe, columns=[f'Var_{i}' for i in range(0, 5)])
    else:
        df = pd.DataFrame(doe, columns=[names[i] for i in range(0, 5)])

    # Créons le pair plot
    n_vars = df.shape[1]
    fig, axes = plt.subplots(n_vars, n_vars, figsize=(14, 12))

    for i in range(n_vars):
        for j in range(n_vars):
            # Diagonal plots
            if i == j:
                axes[i, j].hist(df.iloc[:, i], bins=20, color='gray', alpha=0.6)
                axes[i, j].set_title(df.columns[i])
            else:
                sc = axes[i, j].scatter(df.iloc[:, j], df.iloc[:, i],
                                        c=output, cmap='autumn_r', s=10)
                plt.colorbar(sc, ax=axes[i, j])
                if i == n_vars - 1:
                    axes[i, j].set_xlabel(df.columns[j])
                if j == 0:
                    axes[i, j].set_ylabel(df.columns[i])

    plt.tight_layout()
    if path==None:
        plt.show()
    else:
        plt.savefig(path, dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
        plt.close()



def transform_data(data, threshold, truncated=True):
    th_log = np.log(threshold)
    data_ = np.copy(data)
    data_[data_ < 1e-15] = 1e-15
    response = np.log(data_) * 1.
    if truncated == True:
        response[response < th_log] = th_log
    response_flat = response.reshape((response.shape[0], -1))
    return response, response_flat


def angle_en_crise(W, FB):
    if FB > 2:
        if (W <= 1):
            return 360
        elif (W > 1) and (W <= 3):
            return 130
        elif (W > 3) and (W <= 7):
            return 70
        else:
            return 45
    else:
        if (W <= 1):
            return 360
        elif (W > 1) and (W <= 3):
            return 75
        elif (W > 3) and (W <= 7):
            return 45
        else:
            return 35


def distance_en_crise(W, p, stability, dosetype, threshold):
    if stability == 'DF':
        if (W <= 3):
            if (dosetype == 'Efficace' and threshold == 10):
                return 6500
            elif (dosetype == 'Efficace' and threshold == 50):
                return 2900
            else:
                return 10700
        elif (W > 3):
            if (dosetype == 'Efficace' and threshold == 10):
                return 9700
            elif (dosetype == 'Efficace' and threshold == 50):
                return 4100
            else:
                return 16300

    if stability == 'DN':
        if (W <= 3):
            if (dosetype == 'Efficace' and threshold == 10):
                return 2700
            elif (dosetype == 'Efficace' and threshold == 50):
                return 1200
            else:
                return 4400
        elif (W > 3) and (p < 1):
            if (dosetype == 'Efficace' and threshold == 10):
                return 3900
            elif (dosetype == 'Efficace' and threshold == 50):
                return 1800
            else:
                return 6500
        elif (W > 3) and (p >= 1):
            if (dosetype == 'Efficace' and threshold == 10):
                return 4100
            elif (dosetype == 'Efficace' and threshold == 50):
                return 1800
            else:
                return 6100



def create_cmap(color):
    levels = [0, 1, 2]
    colors = ['white', color]
    cmap, norm = matplotlib.colors.from_levels_and_colors(levels, colors)
    return cmap

def compute_sigma(d, W):
    t = d/W
    if (t < 240.0):
        dA = 0.404469
        dk = 0.859
    elif (t < 97000.0):
        dA = 0.135
        dk = 1.13
    elif (t < 508000.0):
        dA = 0.462975
        dk = 1.0
    elif (t < 1300000.0):
        dA = 6.49907
        dk = 0.824
    else:
        dA = 200177.0
        dk = 0.5

    if d != 0:
        result = 2 * np.arctan(4 * pow(dA * t, dk) / d) * (180./np.pi)
    else:
        result = np.nan
    return result

computesigma = np.vectorize(compute_sigma)

def create_grid_width(distance, width, X, Y, W):
    grid = np.array([[1 if (np.sqrt(X[ii,jj]**2 + Y[ii,jj]**2) <= distance) and
                      ((np.arctan2(Y[ii,jj], X[ii,jj]) * 180/np.pi %360 + 90) %360 - 90 <= (90 + compute_sigma(np.sqrt(Y[ii,jj]**2 + X[ii,jj]**2), W)/2)) and
                      ((np.arctan2(Y[ii,jj], X[ii,jj]) * 180/np.pi %360 + 90) %360 - 90 >= (90 - compute_sigma(np.sqrt(Y[ii,jj]**2 + X[ii,jj]**2), W)/2))
                      else 0
                      for jj in range(X.shape[1])]
                     for ii in range(X.shape[0])])
    return grid



# Fonction pour créer une grille pour chaque portion de cercle
def create_grid_for_sector(X, Y, distance, width):
    # Calcul de la distance de chaque point par rapport à l'origine (0, 0)
    distances = np.sqrt(X**2 + Y**2)

    # Calcul de l'angle de chaque point par rapport à l'axe X (en degrés)
    angles = (np.arctan2(Y, X) * 180 / np.pi + 90) % 360 - 90  # Plage d'angles centrée sur 90°

    # Création de la grille où les points sont dans la portion de cercle définie
    grid = (distances <= distance) * \
           (angles >= (90 - width / 2)) * \
           (angles <= (90 + width / 2))

    return grid



import scipy.interpolate as interp

# Fonction qui fait une seule interpolation sur toutes les données à la fois
def interpolate_and_threshold_doses(doses, CoordX, CoordY, X, Y, threshold):

    # Crée une grille irrégulière à partir de CoordX et CoordY
    points = np.array([CoordX.ravel(), CoordY.ravel()]).T  # Les points d'origine

    # Préparer les points de la grille cible pour interpolation
    target_points = np.array([X.ravel(), Y.ravel()]).T

    # Empile toutes les simulations de doses dans un tableau 2D
    all_doses_ravel = doses.reshape(-1)  # Shape (36 * 62)

    # Applique l'interpolation pour toutes les simulations en une seule passe
    dose_interpolated = interp.griddata(points, all_doses_ravel, target_points, method='linear', fill_value=0)

    # Reshape le résultat pour obtenir (len(Y), len(X))
    dose_interpolated = dose_interpolated.reshape(len(Y), len(X))

    # Conversion en 0/1 selon le seuil
    dose_interpolated_binary = (dose_interpolated > threshold).astype(int)

    return dose_interpolated_binary


if __name__ == "__main__":

    debut = time.time()

    # Vérifier si l'utilisateur a bien passé un argument
    if len(sys.argv) != 2:
        print("Usage: python validate.py <param_file>")
        sys.exit(1)

    # Récupérer le fichier de paramètres depuis les arguments de la ligne de commande
    param_file = sys.argv[1]


    colors_dict = {'crise' : 'darkviolet',
                   'sigma' : 'orange',
                   'emulateur' : 'green',
                   'aamulateur' : 'blue',
                   'aamargulateur' : 'red',
                   }

    # Lecture des données dans le fichier de param
    param = osen.load_parameters(param_file)

    ## Définition des variables de paramètrage
    output_path = param["output_path"]
    doe_path = os.path.join(output_path, "doe")
    result_path = os.path.join(output_path, 'simulations')
    metamodel_path = os.path.join(output_path, 'emulations')
    figure_path = os.path.join(output_path, 'figures')
    simulation_name = param["simulation_name"]
    stability_list = param["stability"]
    FB_list = param["fb"]

    ## Lecture des données de l'émulateur
    aam = pickle.load(open(os.path.join(metamodel_path, 'aam.pickle'), 'rb'))
    krigeage_aam = pickle.load(open(os.path.join(metamodel_path, 'krigeage_aam.pickle'), 'rb'))
    scaler_aam = pickle.load(open(os.path.join(metamodel_path, 'scaler_aam.pickle'), 'rb'))

    ## Lecture des données de l'émulateur
    classification = pickle.load(open(os.path.join(metamodel_path, 'classification.pickle'), 'rb'))
    krigeage = pickle.load(open(os.path.join(metamodel_path, 'krigeage_geometrique.pickle'), 'rb'))
    scaler = pickle.load(open(os.path.join(metamodel_path, 'scaler.pickle'), 'rb'))


    ## Lecture des plans d'expérience
    variable_names, doe_test = osen.read_doe(
        os.path.join(doe_path, "DOE_test.txt"))
    variable_names += ['Amplitude']

    ## Nombre de simulations
    n_test = doe_test.shape[0]

    ## Génération des amplitudes du terme source
    amplitude = [osen.create_double_amplitude(n_test)]

    ## Création du doe complet qui contient les amplitudes
    amplitude_complete = np.array([np.concatenate(
        (amplitude[0][:,0], amplitude[0][:,1]), axis=0)]).T
    doe_complete = np.concatenate(
        (np.concatenate((doe_test, doe_test), axis=0), amplitude_complete),
        axis=1)
    doe_normalized = scaler_aam.transform(doe_complete)

    ## Lecture des coordonnées du maillage
    CoordX = np.load(os.path.join(output_path, 'CoordX.npy'))
    CoordY = np.load(os.path.join(output_path, 'CoordY.npy'))
    R = np.sqrt(CoordX**2 + CoordY**2)
    THETA = np.arctan2(CoordY, CoordX) * 180/np.pi %360
    THETA[:,0] = THETA[:,1]
    shape = R.shape


    from scipy.interpolate import griddata
    x = np.linspace(CoordX.min(), CoordX.max(), 1201)
    y =  np.linspace(CoordY.min(), CoordY.max(), 1201)
    X, Y = np.meshgrid(x,y)
    points = np.array([CoordX.ravel(), CoordY.ravel()]).T


    threshold_list = {"Efficace" : [10, 50], "Inhalation" : [50]}

    ## Boucle sur la dose
    for dosetype in ["Efficace", "Inhalation"]:

        print("- DOSE : " + dosetype)

        ## Boucle sur les stabilités de l'air
        for stability in stability_list:

            print("  - STABILITY : " + stability)

            ## Boucle sur les facteurs de battement de vent
            for FB in FB_list:

                print("    - FB : " + FB)

                threshold = 50

                paths = [os.path.join(output_path, 'simulations/',
                                      simulation_name + "_" + dataset +
                                      "_" + stability + "_FB" + FB)
                         for dataset in ["test"]]

                ## Lecture des résultats de dose
                data = 1e3 * read_simulations(
                    paths, dosetype, amplitude=amplitude)
                dose_simulation, dose_simulation_flat = transform_data(
                    data, 1, truncated=True)

                ## Prediction par Krigeage geométrique
                distance_metamodel1 = np.array([
                    emulateur1(krigeage, classification, scaler, dosetype,
                               stability, FB, threshold,
                              'distance', doe_i) for doe_i in doe_complete])

                width_metamodel1 = np.array([
                    emulateur1(krigeage, classification, scaler, dosetype,
                               stability, FB, threshold,
                              'width', doe_i) for doe_i in doe_complete])

                ## Prediction par Krigeage puis MAA
                score_metamodel2 = np.array([[krigeage_aam[dosetype][stability][FB][ii](doe_i)[0]
                                             for ii in range(9)] for doe_i in doe_normalized])
                score_metamodel2[np.abs(score_metamodel2) > 1e10] = 0
                dose_metamodel2_flat = aam[dosetype][stability][FB].combine(score_metamodel2)
                dose_metamodel2 = dose_metamodel2_flat.reshape(
                    (dose_metamodel2_flat.shape[0], shape[0], shape[1]))


                ## Prediction par FAT
                # distance_fat = np.array([distance_en_crise(doe_i[0], float(FB), stability, dosetype, threshold) for doe_i in doe_complete])
                width_fat = np.array([angle_en_crise(doe_i[0], float(FB)) for doe_i in doe_complete])

                # Initialise des listes pour stocker les faux positifs et négatifs
                false_positives = {'fat': [], 'metamodel1': [], 'metamodel2': [], 'metamodel2_margin': []}
                false_negatives = {'fat': [], 'metamodel1': [], 'metamodel2': [], 'metamodel2_margin': []}
                fms = {'fat': [], 'metamodel1': [], 'metamodel2': [], 'metamodel2_margin': []}

                # Surface d'une cellule en km² (à ajuster selon tes données)
                cell_area_km2 = (50 * 50) / 1e6  # Converti en km²

                for ii in range(len(width_fat)):

                    distance_fat = osen.distance(R, dose_simulation[ii], np.log(threshold), norm='log')

                    depassement_simulation = interpolate_and_threshold_doses(
                        dose_simulation[ii], CoordX, CoordY, X, Y, np.log(threshold))

                    depassement_metamodel2 = interpolate_and_threshold_doses(
                        dose_metamodel2[ii], CoordX, CoordY, X, Y, np.log(threshold))

                    depassement_metamodel2_margin = interpolate_and_threshold_doses(
                        dose_metamodel2[ii], CoordX, CoordY, X, Y, np.log(threshold)/1.1)

                    depassement_metamodel1 = 1. * create_grid_for_sector(X, Y, distance_metamodel1[ii], width_metamodel1[ii])
                    depassement_fat = 1. * create_grid_for_sector(X, Y, distance_fat, width_fat[ii])


                    # Calcul des faux positifs et négatifs en km²
                    for key, depassement in zip(['fat', 'metamodel1', 'metamodel2', 'metamodel2_margin'],
                                                [depassement_fat, depassement_metamodel1, depassement_metamodel2, depassement_metamodel2_margin]):

                        # Faux positifs : simulation = 0, autre = 1
                        fp = ((depassement_simulation == 0) & (depassement == 1)).sum() * cell_area_km2
                        # Faux négatifs : simulation = 1, autre = 0
                        fn = ((depassement_simulation == 1) & (depassement == 0)).sum() * cell_area_km2
                        # FMS
                        ff = ((depassement_simulation == 1) & (depassement == 1)).sum() * cell_area_km2 / \
                            ((depassement_simulation == 1) | (depassement == 1)).sum() * cell_area_km2

                        # Stocker les résultats dans les listes
                        false_positives[key].append(fp)
                        false_negatives[key].append(fn)
                        fms[key].append(ff)

                    # Additionner toutes les grilles pour identifier la région où il y a des valeurs non nulles
                    grid_total = depassement_metamodel2 + depassement_metamodel2_margin + depassement_metamodel1 + depassement_fat

                    # Vérifier si la grille contient des valeurs non nulles
                    if (grid_total > 0).sum() > 0:

                        # Trouver les indices des valeurs non nulles
                        indx, indy = np.where(grid_total > 0)

                        # Calculer les limites Xmax, Xmin, Ymax, Ymin avec une marge de 10%
                        Xmax = (np.max([abs(X[indx, indy].max()), abs(X[indx, indy].min())]) * 1.1) / 1000
                        Xmin = -Xmax
                        Ymax = (abs(Y[indx, indy].max()) * 1.1) / 1000
                        Ymin = -abs(Y[indx, indy].min()) / 1000

                        # Extent pour les imshow
                        extent = [-30, 30, -30, 30]
                        alpha = 0.7

                        # Création de la figure
                        fig = plt.figure(figsize=(8, 8))

                        # Quatrième sous-figure - depassement_fat
                        ax = plt.subplot(221)
                        plt.imshow(depassement_simulation, origin='lower', extent=extent, cmap=create_cmap("Black"))
                        plt.imshow(depassement_fat, origin='lower', extent=extent,
                                   cmap=create_cmap(colors_dict['crise']), alpha=alpha, interpolation='nearest')
                        plt.axis('equal')
                        plt.xlim([Xmin, Xmax])
                        plt.ylim([Ymin, Ymax])
                        plt.xlabel("(a)")

                        # Troisième sous-figure - depassement_metamodel1
                        ax = plt.subplot(222)
                        plt.imshow(depassement_simulation, origin='lower', extent=extent, cmap=create_cmap("Black"))
                        plt.imshow(depassement_metamodel1, origin='lower', extent=extent,
                                   cmap=create_cmap(colors_dict['emulateur']), alpha=alpha, interpolation='nearest')
                        plt.axis('equal')
                        plt.xlim([Xmin, Xmax])
                        plt.ylim([Ymin, Ymax])
                        plt.xlabel("(b)")

                        # Première sous-figure - depassement_metamodel2
                        ax = plt.subplot(223)
                        plt.imshow(depassement_simulation, origin='lower', extent=extent, cmap=create_cmap("Black"))
                        plt.imshow(depassement_metamodel2, origin='lower', extent=extent,
                                   cmap=create_cmap(colors_dict['aamulateur']), alpha=alpha, interpolation='nearest')
                        plt.axis('equal')
                        plt.xlim([Xmin, Xmax])
                        plt.ylim([Ymin, Ymax])
                        plt.xlabel("(c)")

                        # Deuxième sous-figure - depassement_metamodel2_margin
                        ax = plt.subplot(224)
                        plt.imshow(depassement_simulation, origin='lower', extent=extent, cmap=create_cmap("Black"))
                        plt.imshow(depassement_metamodel2_margin, origin='lower', extent=extent,
                                   cmap=create_cmap(colors_dict['aamargulateur']), alpha=alpha, interpolation='nearest')
                        plt.axis('equal')
                        plt.xlim([Xmin, Xmax])
                        plt.ylim([Ymin, Ymax])
                        plt.xlabel("(d)")


                        # Chemin vers le répertoire où sauvegarder la figure
                        output_directory = os.path.join(figure_path, "Comparison_method", dosetype, stability, FB, str(threshold))

                        # Créer le répertoire si nécessaire
                        os.makedirs(output_directory, exist_ok=True)

                        # Sauvegarder la figure dans le répertoire avec le bon nom de fichier
                        plt.savefig(os.path.join(output_directory, "%05d.png" % ii),
                                    dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                        plt.savefig(os.path.join(output_directory, "%05d.pdf" % ii),
                                    dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                        plt.close()



                # Fonction pour calculer la CDF empirique
                def empirical_cdf(data):
                    # Trier les données
                    sorted_data = np.sort(data)
                    # Calculer la CDF : fraction cumulée
                    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
                    return sorted_data, cdf

                # Légendes personnalisées
                legends = ['ATS estimator',
                           'Emulator of geometrical parameters',
                           'Emulation with AAM',
                           'Emulation with AAM and margin']

                # Estimation de la CDF des faux positifs et faux négatifs pour chaque série

                plt.figure(figsize=(6, 7))

                # Faux négatifs
                plt.subplot(2, 1, 1)
                for key, color, legend in zip(['fat', 'metamodel1', 'metamodel2', 'metamodel2_margin'],
                                              ['darkviolet', 'green', 'blue', 'red'],
                                              legends):
                    sorted_fn, cdf_fn = empirical_cdf(false_negatives[key])
                    plt.plot(sorted_fn, cdf_fn, label=legend, color=color)

                # Ajouter les lignes horizontales
                plt.axhline(y=1, color='gray', linestyle='--')
                plt.axhline(y=0.5, color='gray', linestyle='--')
                plt.axhline(y=0, color='gray', linestyle='--')

                plt.xlabel("False Negatives (km²)")
                plt.ylabel("CDF")
                plt.xscale('log')  # Échelle logarithmique pour l'axe X
                plt.legend(loc='lower right')


                # Faux positifs
                plt.subplot(2, 1, 2)
                for key, color, legend in zip(['fat', 'metamodel1', 'metamodel2', 'metamodel2_margin'],
                                              ['darkviolet', 'green', 'blue', 'red'],
                                              legends):
                    sorted_fp, cdf_fp = empirical_cdf(false_positives[key])
                    plt.plot(sorted_fp, cdf_fp, label=legend, color=color)

                # Ajouter les lignes horizontales
                plt.axhline(y=1, color='gray', linestyle='--')
                plt.axhline(y=0.5, color='gray', linestyle='--')
                plt.axhline(y=0, color='gray', linestyle='--')

                plt.xlabel("False Positives (km²)")
                plt.ylabel("CDF")
                plt.xscale('log')  # Échelle logarithmique pour l'axe X
                plt.legend(loc='lower right')


                # Sauvegarder la figure dans le répertoire avec le bon nom de fichier
                plt.savefig(
                    os.path.join(
                        figure_path,"cdf_" + dosetype + "_" + stability + "_FB" + FB +
                        "_" + str(threshold) + ".pdf"),
                    dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                plt.savefig(
                    os.path.join(
                        figure_path,"cdf_" + dosetype + "_" + stability + "_FB" + FB +
                        "_" + str(threshold) + ".png"),
                    dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                plt.close()



                # Calcul de la somme des faux positifs et faux négatifs pour chaque méthode
                total_false_positives = {
                    'ATS estimator': np.sum(false_positives['fat']) * cell_area_km2,
                    'Emulator of geometrical parameters': np.sum(false_positives['metamodel1']) * cell_area_km2,
                    'Emulation with AAM': np.sum(false_positives['metamodel2']) * cell_area_km2,
                    'Emulation with AAM and margin': np.sum(false_positives['metamodel2_margin']) * cell_area_km2,
                }

                total_false_negatives = {
                    'ATS estimator': np.sum(false_negatives['fat']) * cell_area_km2,
                    'Emulator of geometrical parameters': np.sum(false_negatives['metamodel1']) * cell_area_km2,
                    'Emulation with AAM': np.sum(false_negatives['metamodel2']) * cell_area_km2,
                    'Emulation with AAM and margin': np.sum(false_negatives['metamodel2_margin']) * cell_area_km2,
                }

                # Création du tableau avec les données calculées
                data = {
                    'Estimator': ['ATS estimator',
                                  'Emulator of geometrical parameters',
                                  'Emulation with AAM',
                                  'Emulation with AAM and margin'],
                    'False-Positive (km²)': [
                        total_false_positives['ATS estimator'],
                        total_false_positives['Emulator of geometrical parameters'],
                        total_false_positives['Emulation with AAM'],
                        total_false_positives['Emulation with AAM and margin']],
                    'False-Negative (km²)': [
                        total_false_negatives['ATS estimator'],
                        total_false_negatives['Emulator of geometrical parameters'],
                        total_false_negatives['Emulation with AAM'],
                        total_false_negatives['Emulation with AAM and margin']]
                }

                # Créer un DataFrame pandas
                df = pd.DataFrame(data)

                # Afficher le tableau avec pandas
                print(df)
