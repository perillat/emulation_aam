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
import matplotlib.ticker as ticker

## Script to create emulators from previously run simulations.

def emulateur(krigeage, aam, scaler, dosetype, stability, shape, inputs):

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
    Reads simulation files from one or multiple given directories
    and returns a concatenation of the results.

    Args:
        sim_path (str or list of str): Path(s) to the directory/directories
        containing the simulation files.
        dosetype (str, optional): Type of dose to read, default is "Efficace".
        amplitude (list, optional): Amplitude of the source term to be used
        with the data.

    Returns:
        np.ndarray: 3D NumPy array containing the results of all simulations.

    Raises:
        ValueError: If sim_path is neither a string nor a list of strings.

    """
    ## Check the format of sim_path
    if type(sim_path) == str:
        paths = [sim_path]
    elif type(sim_path) == list:
        paths = sim_path
    else:
        print("Error: sim_path must be a string or a list of string")


    ## Initialize the dictionary
    simulations = {}

    ## Loop through directories
    for ipath, path in enumerate(paths):

        lenght_ = lenght

        first_pass = True
        dir_list = os.listdir(path)
        n_dataset = len(dir_list)

        ## Use the corresponding amplitude
        if amplitude == None:
            ampli = 100. * np.ones(n_dataset)
        else:
            ampli = amplitude[ipath]

        if lenght_ == None:
            lenght_ = n_dataset

        ## Loop through the simulations in the directory
        for idir, dirname in enumerate(sorted(dir_list)[:lenght_]):

            ## Read the file
            file_path = os.path.join(path, dirname, "Dose_"+dosetype+".npy")
            #print(format_file_path(file_path))
            dose = np.load(file_path)

            ## Initialize the array
            if first_pass:
                shape = dose.shape
                simulations[path] = np.zeros((ampli.shape[1] * lenght_, shape[1], shape[2]))
                first_pass = False

            ## Extract the value at the last time step
            for copy in range(ampli.shape[1]):
                simulations[path][copy * lenght_ + idir,:,:] = \
                    dose[-1, :, :] * ampli[idir,copy]/100.

    # Concatenate all results from different paths
    return np.concatenate(list(simulations.values()), axis=0)


def pair_plot(doe, output, names=None, path=None):

    # Convert the numpy array to a DataFrame for better column handling
    if names==None:
        df = pd.DataFrame(doe, columns=[f'Var_{i}' for i in range(0, 5)])
    else:
        df = pd.DataFrame(doe, columns=[names[i] for i in range(0, 5)])

    # Create the pair plot
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


if __name__ == "__main__":

    debut = time.time()

    # Check if the user has provided an argument
    if len(sys.argv) != 2:
        print("Usage: python validate.py <param_file>")
        sys.exit(1)

    # Retrieve the parameter file from command line arguments
    param_file = sys.argv[1]

    # Read data from the parameter file
    param = osen.load_parameters(param_file)

    ## Define configuration variables
    output_path = param["output_path"]
    doe_path = os.path.join(output_path, "doe")
    result_path = os.path.join(output_path, 'simulations')
    metamodel_path = os.path.join(output_path, 'emulations')
    figure_path = os.path.join(output_path, 'figures')
    simulation_name = param["simulation_name"]
    stability_list = param["stability"]
    FB_list = param["fb"]

    ## Load emulator data
    aam = pickle.load(open(os.path.join(metamodel_path, 'aam.pickle'), 'rb'))
    krigeage = pickle.load(open(os.path.join(metamodel_path, 'krigeage_aam.pickle'), 'rb'))
    scaler = pickle.load(open(os.path.join(metamodel_path, 'scaler_aam.pickle'), 'rb'))

    ## Read the design of experiments
    variable_names, doe_test = osen.read_doe(
        os.path.join(doe_path, "DOE_test.txt"))
    variable_names += ['Amplitude']

    ## Number of simulations
    n_test = doe_test.shape[0]

    ## Generate source term amplitudes
    amplitude = [osen.create_double_amplitude(n_test)]

    ## Create the complete DOE that includes amplitudes
    amplitude_complete = np.array([np.concatenate(
        (amplitude[0][:,0], amplitude[0][:,1]), axis=0)]).T
    doe_complete = np.concatenate(
        (np.concatenate((doe_test, doe_test), axis=0), amplitude_complete),
        axis=1)
    doe_normalized = scaler.transform(doe_complete)

    ## Read the mesh coordinates
    CoordX = np.load(os.path.join(output_path, 'CoordX.npy'))
    CoordY = np.load(os.path.join(output_path, 'CoordY.npy'))
    R = np.sqrt(CoordX**2 + CoordY**2)
    THETA = np.arctan2(CoordY, CoordX) * 180/np.pi %360
    THETA[:,0] = THETA[:,1]
    shape = R.shape
    points = np.array([CoordX.ravel(), CoordY.ravel()]).T

    threshold_list = {"Efficace" : [10, 50], "Inhalation" : [50]}

    ## Loop over dose types
    for dosetype in ["Inhalation"]: #["Efficace", "Inhalation"]:

        print("- DOSE : " + dosetype)

        ## Loop over air stabilities
        for stability in ["DN"]: #stability_list:

            print("  - STABILITY : " + stability)

            ## Loop over wind beating factors
            for FB in ["3"]: #FB_list:

                print("    - FB : " + FB)

                paths = [os.path.join(output_path, 'simulations/',
                                      simulation_name + "_" + dataset +
                                      "_" + stability + "_FB" + FB)
                         for dataset in ["test"]]

                ## Read dose results
                data = 1e3 * read_simulations(
                    paths, dosetype, amplitude=amplitude)
                dose_simulation, dose_simulation_flat = transform_data(
                    data, 1, truncated=True)
                ## Projection using AAM
                _, score_simulation = aam[dosetype][stability][FB].project(
                    dose_simulation_flat)
                score_simulation[np.abs(score_simulation)> 1e10] = 0
                dose_projection_flat = aam[dosetype][stability][FB].combine(score_simulation)
                dose_projection = dose_projection_flat.reshape(
                    (dose_projection_flat.shape[0], shape[0], shape[1]))

                ## Prediction using Kriging and then AMM
                score_metamodel = np.array([[krigeage[dosetype][stability][FB][ii](doe_i)[0]
                                             for ii in range(9)] for doe_i in doe_normalized])
                score_metamodel[np.abs(score_metamodel) > 1e10] = 0
                dose_metamodel_flat = aam[dosetype][stability][FB].combine(score_metamodel)
                dose_metamodel = dose_metamodel_flat.reshape(
                    (dose_metamodel_flat.shape[0], shape[0], shape[1]))

                ## Plot scores from Kriging
                fig = plt.figure(figsize=(11,11))
                smse = np.empty(9)

                with open(os.path.join(figure_path, "score_"+dosetype+"_"+stability+
                                       "_FB"+FB+".txt"), "w") as file:
                    for ii in range(score_simulation.shape[1]):
                        ax = plt.subplot(3, 3, ii+1)
                        x_percentiles = np.percentile(score_simulation[:, ii], [1, 99])
                        y_percentiles = np.percentile(score_metamodel[:, ii], [1, 99])
                        xmin, xmax = x_percentiles * 1.1
                        ymin, ymax = y_percentiles * 1.1
                        ax.plot(score_simulation[:, ii], score_metamodel[:, ii], '.b',
                                label="Score n°%1d"%(ii+1))
                        x_line = np.linspace(min(xmin, ymin), max(xmax, ymax), 100)
                        ax.plot(x_line, x_line, linestyle='--', color='k')
                        plt.axis('equal')
                        ax.set_xlim(xmin, xmax)
                        ax.set_ylim(ymin, ymax)
                        ax.legend(loc="upper left")

                        smse[ii] = np.nansum((score_simulation[:, ii] - score_metamodel[:, ii])**2) / \
                            np.nansum((score_simulation[:, ii] - np.nanmean(score_simulation[:, ii]))**2)
                        file.write(f"SMSE score {(ii+1):02d} : {smse[ii]:.03e}\n")

                plt.savefig(os.path.join(
                    figure_path, "score_"+dosetype+"_"+stability+"_FB"+FB+".png"),
                            dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                plt.savefig(os.path.join(
                    figure_path, "score_"+dosetype+"_"+stability+"_FB"+FB+".pdf"),
                            dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                plt.close()


                ## Comparison of dose at each point
                fig = plt.figure(figsize=(11,5))
                ax1 = plt.subplot(121)
                plt.plot(dose_simulation.ravel(), dose_metamodel.ravel(), '.b')
                plt.xlabel("Dose simulée (Ln(mSv))")
                plt.ylabel("Dose émulée (Ln(mSv))")
                xmin, xmax = ax1.get_xlim()
                ymin, ymax = ax1.get_ylim()
                x_line = np.linspace(min(xmin, ymin), max(xmax, ymax), 100)
                plt.plot(x_line, x_line, label='y=x', linestyle='--', color='k')
                ax1.set_xlim(xmin, xmax)
                ax1.set_ylim(ymin, ymax)
                error = (dose_metamodel.ravel() - dose_simulation.ravel())
                MEA = np.mean(np.abs(error))
                Q95 = np.percentile(np.abs(error), 95)
                ax2 = plt.subplot(122)
                plt.hist(error, bins=np.linspace(-0.2, 0.2, 41), density=True)
                plt.xlabel("Erreur (Ln(mSv))")
                plt.ylabel("Fréquence")
                text_str = f"MEA: {MEA:.2f} Ln(mSv)\nQ95: {Q95:.2f} Ln(mSv)"
                props = dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.5)
                ax2.text(0.05, 0.95, text_str, transform=ax2.transAxes, fontsize=10,
                         verticalalignment='top', bbox=props)
                plt.savefig(os.path.join(
                figure_path, "dose_"+dosetype+"_"+stability+"_FB"+FB+".png"),
                            dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                plt.savefig(os.path.join(
                figure_path, "dose_"+dosetype+"_"+stability+"_FB"+FB+".pdf"),
                            dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                plt.close()


                ## Graph 2D
                th = np.log(50)

                # Simulation vs Metamodel
                for ii in range(dose_simulation.shape[0]):

                    fig, axs = plt.subplots(1, 2, figsize=(12, 5), constrained_layout=True)

                    CoordX0 = np.vstack([CoordX, CoordX[0,:]])
                    CoordY0 = np.vstack([CoordY, CoordY[0,:]])
                    data_to_plot1 = np.vstack([dose_simulation[ii], dose_simulation[ii,0,:]])
                    data_to_plot2 = np.vstack([dose_metamodel[ii], dose_metamodel[ii,0,:]])
                    data_to_plot2[data_to_plot2 < 0] = 0

                    levels = list(th * np.linspace(0, 2, 11))

                    # Premier subplot
                    ax1 = axs[0]
                    contour1 = ax1.contourf(CoordX0 / 1000, CoordY0 / 1000, data_to_plot1, levels=levels, extend='max')
                    if data_to_plot1.max() > th:
                        ax1.contour(CoordX0 / 1000, CoordY0 / 1000, data_to_plot1, levels=[th], colors='red')
                    ax1.set_xlim((-4, 4))
                    ax1.set_ylim((-1, 7.5))


                    # Deuxième subplot
                    ax2 = axs[1]
                    contour2 = ax2.contourf(CoordX0 / 1000, CoordY0 / 1000, data_to_plot2, levels=levels, extend='max')
                    if data_to_plot2.max() > th:
                        ax2.contour(CoordX0 / 1000, CoordY0 / 1000, data_to_plot2, levels=[th], colors='red')
                    ax2.set_xlim((-4, 4))
                    ax2.set_ylim((-1, 7.5))

                    # Ajout de la colorbar commune
                    cbar = fig.colorbar(contour2, ax=axs, orientation='vertical', fraction=0.02, pad=0.04)

                    # Fonction pour transformer le log(dose) en dose réelle
                    def log_to_dose(val, pos):
                        dose_real = np.exp(val)
                        return f"{dose_real:.1f}"

                    # Appliquer la transformation aux ticks de la colorbar
                    cbar.set_ticks(levels)
                    cbar.ax.yaxis.set_major_formatter(ticker.FuncFormatter(log_to_dose))

                    # Mise à jour du label de la colorbar
                    cbar.set_label("Dose rate (mSv)")

                    osen.makedir(os.path.join(figure_path, dosetype, stability, FB))
                    plt.savefig(os.path.join(figure_path, dosetype, stability, FB, "%05d.png" %ii),
                                dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                    plt.savefig(os.path.join(figure_path, dosetype, stability, FB, "%05d.pdf" %ii),
                                dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                    plt.close()



                # Simulation vs Projection
                for ii in [5]:

                    fig, axs = plt.subplots(1, 2, figsize=(6, 2.5), constrained_layout=True)

                    CoordX0 = np.vstack([CoordX, CoordX[0,:]])
                    CoordY0 = np.vstack([CoordY, CoordY[0,:]])
                    data_to_plot1 = np.vstack([dose_simulation[ii], dose_simulation[ii,0,:]])
                    data_to_plot2 = np.vstack([dose_projection[ii], dose_projection[ii,0,:]])
                    data_to_plot2[data_to_plot2 < 0] = 0

                    levels = list(th * np.linspace(0, 2, 11))

                    # Premier subplot
                    ax1 = axs[0]
                    contour1 = ax1.contourf(CoordX0 / 1000, CoordY0 / 1000, data_to_plot1, levels=levels, extend='max')
                    if data_to_plot1.max() > th:
                        ax1.contour(CoordX0 / 1000, CoordY0 / 1000, data_to_plot1, levels=[th], colors='red')
                    ax1.set_xlim((-4, 4))
                    ax1.set_ylim((-1, 7.5))

                    # Deuxième subplot
                    ax2 = axs[1]
                    contour2 = ax2.contourf(CoordX0 / 1000, CoordY0 / 1000, data_to_plot2, levels=levels, extend='max')
                    if data_to_plot2.max() > th:
                        ax2.contour(CoordX0 / 1000, CoordY0 / 1000, data_to_plot2, levels=[th], colors='red')
                    ax2.set_xlim((-4, 4))
                    ax2.set_ylim((-1, 7.5))

                    # Ajout de la colorbar commune
                    cbar = fig.colorbar(contour2, ax=axs, orientation='vertical', fraction=0.02, pad=0.04)

                    # Fonction pour transformer le log(dose) en dose réelle
                    def log_to_dose(val, pos):
                        dose_real = np.exp(val)
                        return f"{dose_real:.1f}"

                    # Appliquer la transformation aux ticks de la colorbar
                    cbar.set_ticks(levels)
                    cbar.ax.yaxis.set_major_formatter(ticker.FuncFormatter(log_to_dose))

                    # Mise à jour du label de la colorbar
                    cbar.set_label("Dose rate (mSv)")

                    osen.makedir(os.path.join(figure_path, dosetype, stability, FB))
                    plt.savefig(os.path.join(figure_path, dosetype, stability, FB, "%05d_projection.png" %ii),
                                dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                    plt.savefig(os.path.join(figure_path, dosetype, stability, FB, "%05d_projection.pdf" %ii),
                                dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                    plt.close()



                ## Plots the 4 figures

                # Sélectionner les indices des simulations à tracer
                indices = [5, 62, 251, 216]

                # Création de la figure principale avec 4 lignes et 2 colonnes
                fig, axs = plt.subplots(4, 2, figsize=(9, 20), constrained_layout=True)

                # Ajustement des espaces entre les subplots pour éviter l'écrasement
                plt.subplots_adjust(hspace=0.3, wspace=0.1)

                # Valeur du seuil en log
                th = np.log(50)

                # Définition des niveaux pour la colorbar
                levels = list(th * np.linspace(0, 2, 11))

                # Labels des sous-figures
                subplot_labels = ['(a)', '(b)', '(c)', '(d)', '(e)', '(f)', '(g)', '(h)']

                # Boucle sur les 4 jeux de données
                for row, ii in enumerate(indices):
                    CoordX0 = np.vstack([CoordX, CoordX[0, :]])
                    CoordY0 = np.vstack([CoordY, CoordY[0, :]])
                    data_to_plot1 = np.vstack([dose_simulation[ii], dose_simulation[ii, 0, :]])
                    data_to_plot2 = np.vstack([dose_metamodel[ii], dose_metamodel[ii, 0, :]])
                    data_to_plot2[data_to_plot2 < 0] = 0

                    # Premier subplot de la ligne
                    ax1 = axs[row, 0]
                    contour1 = ax1.contourf(CoordX0 / 1000, CoordY0 / 1000, data_to_plot1, levels=levels, extend='max')
                    if data_to_plot1.max() > th:
                        ax1.contour(CoordX0 / 1000, CoordY0 / 1000, data_to_plot1, levels=[th], colors='red')
                    ax1.set_xlim((-4, 4))
                    ax1.set_ylim((-1, 7.5))

                    # Deuxième subplot de la ligne
                    ax2 = axs[row, 1]
                    contour2 = ax2.contourf(CoordX0 / 1000, CoordY0 / 1000, data_to_plot2, levels=levels, extend='max')
                    if data_to_plot2.max() > th:
                        ax2.contour(CoordX0 / 1000, CoordY0 / 1000, data_to_plot2, levels=[th], colors='red')
                    ax2.set_xlim((-4, 4))
                    ax2.set_ylim((-1, 7.5))

                    # Ajouter les labels sous les figures
                    ax1.annotate(subplot_labels[row * 2], xy=(0.5, -0.15), xycoords='axes fraction',
                                 fontsize=14, ha='center', fontweight='bold')
                    ax2.annotate(subplot_labels[row * 2 + 1], xy=(0.5, -0.15), xycoords='axes fraction',
                                 fontsize=14, ha='center', fontweight='bold')

                # Ajout d'une colorbar commune
                cbar = fig.colorbar(contour2, ax=axs[:, 1], orientation='vertical', fraction=0.02, pad=0.04)

                # Fonction pour transformer le log(dose) en dose réelle
                def log_to_dose(val, pos):
                    dose_real = np.exp(val)
                    return f"{dose_real:.1f}"

                # Appliquer la transformation aux ticks de la colorbar
                cbar.set_ticks(levels)
                cbar.ax.yaxis.set_major_formatter(ticker.FuncFormatter(log_to_dose))
                cbar.set_label("Dose rate (mSv)")

                # Sauvegarde de la figure combinée
                plt.savefig(os.path.join(figure_path, dosetype, stability, FB, "combined_figure.png"),
                            dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                plt.savefig(os.path.join(figure_path, dosetype, stability, FB, "combined_figure.pdf"),
                            dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)

                plt.show()




                ## FMS (histogram)

                points_list, unique_indices = np.unique(
                    np.array([CoordX.ravel(), CoordY.ravel()]).T, axis=0, return_index=True)

                # Voronoï diagram
                vor = Voronoi(points_list)
                areas = []
                for region in vor.regions:
                    if -1 in region:
                        areas.append(0)
                    else:
                        if len(region) > 0:
                            polygon = Polygon([vor.vertices[i] for i in region])
                            if polygon.is_valid:
                                areas.append(polygon.area/1e6)

                grid_simulation = dose_simulation.reshape(
                    (dose_simulation.shape[0], -1))[:, unique_indices]
                grid_metamodel = dose_metamodel.reshape(
                    (dose_metamodel.shape[0], -1))[:, unique_indices]
                grid_projection = dose_projection.reshape(
                    (dose_projection.shape[0], -1))[:, unique_indices]

                for threshold in threshold_list[dosetype]:

                    boolean_simulation = (grid_simulation >= np.log(threshold))
                    boolean_metamodel = (grid_metamodel >= np.log(threshold))
                    boolean_projection = (grid_projection >= np.log(threshold))

                    boolean_and = np.logical_and(boolean_simulation, boolean_metamodel)
                    boolean_or = np.logical_or(boolean_simulation, boolean_metamodel)

                    fms = ((boolean_and * np.array(areas)).sum(axis=1) /
                           (boolean_or  * np.array(areas)).sum(axis=1))

                    print("Pourcentage de FMS entre 0.8 et 1 : " + str(np.sum(fms >= 0.8)*100/len(fms) ))
                    print("Pourcentage de FMS = NaN : " + str(np.sum(np.isnan(fms))*100/len(fms) ))
                    print("Pourcentage de FMS = 0 : " + str(np.sum(fms == 0)*100/len(fms) ))
                    print("Pourcentage de FMS autre : " + str(100 - np.sum(fms >= 0.8)*100/len(fms) - np.sum(np.isnan(fms))*100/len(fms) - np.sum(fms == 0)*100/len(fms) ))

                    fig = plt.figure(figsize=(5,4))
                    ax = plt.subplot(111)
                    plt.hist(fms, bins=np.linspace(0,1,21))
                    plt.xlim((0,1))
                    plt.xlabel("FMS")
                    plt.ylabel("Frequence")
                    plt.savefig(os.path.join(
                        figure_path, "FMS_metamodel_" + dosetype + "_" + stability + "_FB" + FB +
                        "_" + str(threshold) + ".png"),
                                dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                    plt.savefig(os.path.join(
                        figure_path, "FMS_metamodel_" + dosetype + "_" + stability + "_FB" + FB +
                        "_" + str(threshold) + ".pdf"),
                                dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                    plt.close()


                    boolean_and = np.logical_and(boolean_simulation, boolean_projection)
                    boolean_or = np.logical_or(boolean_simulation, boolean_projection)

                    fms = ((boolean_and * np.array(areas)).sum(axis=1) /
                           (boolean_or  * np.array(areas)).sum(axis=1))

                    fig = plt.figure(figsize=(5,4))
                    ax = plt.subplot(111)
                    plt.hist(fms, bins=np.linspace(0,1,21))
                    plt.xlim((0,1))
                    plt.xlabel("FMS")
                    plt.ylabel("Frequence")
                    plt.savefig(os.path.join(
                        figure_path, "FMS_projection_" + dosetype + "_" + stability + "_FB" + FB +
                        "_" + str(threshold) + ".png"),
                                dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                    plt.savefig(os.path.join(
                        figure_path, "FMS_projection_" + dosetype + "_" + stability + "_FB" + FB +
                        "_" + str(threshold) + ".pdf"),
                                dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                    plt.close()





                    surface_simulation = (grid_simulation > np.log(threshold)) * areas
                    surface_metamodel = (grid_metamodel > np.log(threshold)) * areas
                    s_simu = surface_simulation.sum(axis=1)
                    s_meta = surface_metamodel.sum(axis=1)

                    fig = plt.figure(figsize=(6,5))
                    ax1 = plt.subplot(111)
                    plt.plot(s_simu, s_meta, '.b')
                    plt.xlabel("Surface simulée (m²)")
                    plt.ylabel("Surface estimée (m²)")
                    xmin, xmax = ax1.get_xlim()
                    ymin, ymax = ax1.get_ylim()
                    x_line = np.linspace(min(xmin, ymin), max(xmax, ymax), 100)
                    plt.plot(x_line, x_line, label='y=x', linestyle='--', color='k')
                    ax1.set_xlim(xmin, xmax)
                    ax1.set_ylim(ymin, ymax)
                    plt.savefig(os.path.join(
                        figure_path, "surface_" + dosetype + "_" + stability + "_FB" + FB +
                        "_" + str(threshold) + ".png"),
                                dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                    plt.savefig(os.path.join(
                        figure_path, "surface_" + dosetype + "_" + stability + "_FB" + FB +
                        "_" + str(threshold) + ".pdf"),
                                dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                    plt.close()



                    fig = plt.figure(figsize=(11,5))
                    ax1 = plt.subplot(121)
                    plt.plot(s_simu, s_meta, '.b')
                    plt.xlabel("Surface simulée (km²)")
                    plt.ylabel("Surface émulée (km²)")
                    xmin, xmax = ax1.get_xlim()
                    ymin, ymax = ax1.get_ylim()
                    x_line = np.linspace(min(xmin, ymin), max(xmax, ymax), 100)
                    plt.plot(x_line, x_line, label='y=x', linestyle='--', color='k')
                    ax1.set_xlim(xmin, xmax)
                    ax1.set_ylim(ymin, ymax)
                    error = (s_meta - s_simu)
                    MEA = np.mean(np.abs(error))
                    Q95 = np.percentile(np.abs(error), 95)
                    ax2 = plt.subplot(122)
                    plt.hist((s_meta-s_simu), bins=np.linspace(-5.5, 5.5, 12), density=True)
                    plt.xlabel("Erreur (km²)")
                    plt.ylabel("Fréquence")
                    text_str = f"MEA: {MEA:.2f} km\nQ95: {Q95:.2f} km"
                    props = dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.5)
                    ax2.text(0.05, 0.95, text_str, transform=ax2.transAxes, fontsize=10,
                             verticalalignment='top', bbox=props)
                    plt.savefig(
                        os.path.join(
                            figure_path,"distance_" + dosetype + "_" + stability + "_FB" + FB +
                            "_" + str(threshold) + ".png"),
                        dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                    plt.savefig(
                        os.path.join(
                            figure_path,"distance_" + dosetype + "_" + stability + "_FB" + FB +
                            "_" + str(threshold) + ".pdf"),
                        dpi=300, facecolor="w", bbox_inches="tight", pad_inches=0.05)
                    plt.close()


    fin = time.time()
    print("Emulators validated in %.02f seconds" %(fin-debut))
