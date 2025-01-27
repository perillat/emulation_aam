# -*- coding: utf-8 -*-
import os, sys
import osen
import time
import numpy as np
from sklearn.preprocessing import MinMaxScaler
import openturns as ot
import pickle
from autoassociativemodel.autoassociativemodel import AutoAssociativeModel


## Script to create emulators with MAA from previously run simulations.

def format_file_path(file_path, total_length=80):
    prefix = "Reading file : "
    if len(prefix + file_path) > total_length:
        over_by = len(prefix + file_path) - total_length + 3  # +3 pour "...".
        file_path = "..." + file_path[-(len(file_path) - over_by):]
    return prefix + file_path

def read_simulations(sim_path, dosetype="Efficace", amplitude=None, lenght=None):
    """
    Reads simulation files from one or multiple directories and returns a concatenation of results.

    Args:
        sim_path (str or list of str): Path(s) to the directory/directories containing simulation files.
        dosetype (str, optional): Type of dose to read, default is "Efficace".
        amplitude (list, optional): Source term amplitude to use with the data.

    Returns:
        np.ndarray: 3D NumPy array containing the results of all simulations.

    Raises:
        ValueError: If sim_path is neither a string nor a list of strings.

    """
    ## Checking the format of sim_path
    if type(sim_path) == str:
        paths = [sim_path]
    elif type(sim_path) == list:
        paths = sim_path
    else:
        print("Error: sim_path must be a string or a list of string")


    ## Initializing the dictionary
    simulations = {}

    ## Loop through directories
    for ipath, path in enumerate(paths):

        lenght_ = lenght

        first_pass = True
        dir_list = os.listdir(path)
        n_dataset = len(dir_list)

        ## Using the corresponding amplitude
        if amplitude == None:
            ampli = 100. * np.ones(n_dataset)
        else:
            ampli = amplitude[ipath]

        if lenght_ == None:
            lenght_ = n_dataset

        ## Loop through the simulations in the directory
        for idir, dirname in enumerate(sorted(dir_list)[:lenght_]):

            ## Reading the file
            file_path = os.path.join(path, dirname, "Dose_"+dosetype+".npy")
            dose = np.load(file_path)

            ## Initializing the array
            if first_pass:
                shape = dose.shape
                simulations[path] = np.zeros((ampli.shape[1] * lenght_, shape[1], shape[2]))
                first_pass = False

            ## Extracting the value at the last time step
            for copy in range(ampli.shape[1]):
                simulations[path][copy * lenght_ + idir,:,:] = \
                    dose[-1, :, :] * ampli[idir,copy]/100.

    # Concatenating all results from different paths
    return np.concatenate(list(simulations.values()), axis=0)



def transform_data(data, threshold, truncated=True):
    """
    Transforms the data into logarithmic scale and optionally truncates it.

    Args:
        data (np.ndarray): The data to transform.
        threshold (float): Minimum value for truncation.
        truncated (bool, optional): Whether to truncate the data. Defaults to True.

    Returns:
        tuple: Transformed data and its flattened version.
    """
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

    # Checking if the user provided an argument
    if len(sys.argv) != 2:
        print("Usage: python create.py <param_file>")
        sys.exit(1)

    # Retrieving the parameter file from command line arguments
    param_file = sys.argv[1]

    # Reading data from the parameter file
    param = osen.load_parameters(param_file)

    ## Setting configuration variables
    output_path = param["output_path"]
    simulation_name = param["simulation_name"]
    stability_list = param["stability"] if isinstance(param["stability"], list) else [param["stability"]]
    FB_list = param["fb"] if isinstance(param["fb"], list) else [param["fb"]]
    doe_path = os.path.join(output_path, "doe")

    ## Reading design of experiments
    variable_names, doe_train = osen.read_doe(
        os.path.join(doe_path, "DOE_train.txt"))
    variable_names, doe_test = osen.read_doe(
        os.path.join(doe_path, "DOE_test.txt"))
    variable_names, doe_fit = osen.read_doe(
        os.path.join(doe_path, "DOE_fit.txt"))

    ## Number of simulations
    n_train = doe_train.shape[0]
    n_test = doe_test.shape[0]
    n_fit = doe_fit.shape[0]

    ## Generating source term amplitudes
    amplitude_train = [osen.create_double_amplitude(n_train)]
    amplitude_complete_train = np.array([np.concatenate(
        (amplitude_train[0][:,0], amplitude_train[0][:,1]), axis=0)]).T
    amplitude_test = [osen.create_double_amplitude(n_test)]
    amplitude_complete_test = np.array([np.concatenate(
        (amplitude_test[0][:,0], amplitude_test[0][:,1]), axis=0)]).T
    amplitude_fit = [osen.create_double_amplitude(n_fit)]
    amplitude_complete_fit = np.array([np.concatenate(
        (amplitude_fit[0][:,0], amplitude_fit[0][:,1]), axis=0)]).T

    doe_train = np.concatenate(
        (np.concatenate((doe_train, doe_train), axis=0),
            amplitude_complete_train), axis=1)
    doe_test = np.concatenate(
        (np.concatenate((doe_test, doe_test), axis=0),
            amplitude_complete_test), axis=1)
    doe_fit = np.concatenate(
        (np.concatenate((doe_fit, doe_fit), axis=0),
            amplitude_complete_fit), axis=1)

    # Normalizing the design of experiments
    scaler = MinMaxScaler()
    doe_normalized_train = scaler.fit_transform(doe_train)
    doe_normalized_test = scaler.transform(doe_test)
    doe_normalized_fit = scaler.transform(doe_fit)

    ## Reading mesh coordinates
    CoordX = np.load(os.path.join(output_path, 'CoordX.npy'))
    CoordY = np.load(os.path.join(output_path, 'CoordY.npy'))
    R = np.sqrt(CoordX**2 + CoordY**2)
    THETA = np.arctan2(CoordY, CoordX) * 180/np.pi %360
    THETA[:,0] = THETA[:,1]

    threshold_list = {"Efficace" : [10, 50], "Inhalation" : [50]}

    ## Reading dose data
    dose_train = {}
    dose_train_transform = {}
    dose_train_transform_flat = {}
    dose_test = {}
    dose_test_transform = {}
    dose_test_transform_flat = {}
    dose_fit = {}
    dose_fit_transform = {}
    dose_fit_transform_flat = {}
    aam = {}
    score = {}
    krigeage = {}

    print("Reading files...")

    ## Loop over doses
    for dosetype in ["Efficace", "Inhalation"]:

        print("- DOSE : " + dosetype)

        dose_train[dosetype] = {}
        dose_train_transform[dosetype] = {}
        dose_train_transform_flat[dosetype] = {}

        dose_test[dosetype] = {}
        dose_test_transform[dosetype] = {}
        dose_test_transform_flat[dosetype] = {}

        dose_fit[dosetype] = {}
        dose_fit_transform[dosetype] = {}
        dose_fit_transform_flat[dosetype] = {}

        aam[dosetype] = {}
        score[dosetype] = {}
        krigeage[dosetype] = {}

        ## Loop over air stabilities
        for stability in stability_list:

            print("  - STABILITY : " + stability)

            dose_train[dosetype][stability] = {}
            dose_train_transform[dosetype][stability] = {}
            dose_train_transform_flat[dosetype][stability] = {}

            dose_test[dosetype][stability] = {}
            dose_test_transform[dosetype][stability] = {}
            dose_test_transform_flat[dosetype][stability] = {}

            dose_fit[dosetype][stability] = {}
            dose_fit_transform[dosetype][stability] = {}
            dose_fit_transform_flat[dosetype][stability] = {}

            aam[dosetype][stability] = {}
            score[dosetype][stability] = {}
            krigeage[dosetype][stability] = {}

            ## Loop over wind beating factors
            for FB in FB_list:

                print("    - FB : " + str(FB))

                ## Directories containing training data
                paths_train = [os.path.join(output_path, 'simulations/',
                                            simulation_name + "_" + dataset +
                                            "_" + stability + "_FB" + str(FB))
                               for dataset in ["train"]]
                paths_test = [os.path.join(output_path, 'simulations/',
                                           simulation_name + "_" + dataset +
                                           "_" + stability + "_FB" + str(FB))
                              for dataset in ["test"]]
                paths_fit = [os.path.join(output_path, 'simulations/',
                                          simulation_name + "_" + dataset +
                                          "_" + stability + "_FB" + str(FB))
                              for dataset in ["fit"]]

                ## Reading dose results
                dose_train[dosetype][stability][FB] = 1e3 * read_simulations(
                    paths_train, dosetype, amplitude=amplitude_train)
                dose_test[dosetype][stability][FB] = 1e3 * read_simulations(
                    paths_test,dosetype, amplitude=amplitude_test)
                dose_fit[dosetype][stability][FB] = 1e3 * read_simulations(
                    paths_fit,dosetype, amplitude=amplitude_fit)

                ## Logarithmic transformation of doses and truncation at 1
                _, dose_train_transform_flat[dosetype][stability][FB] = transform_data(
                    dose_train[dosetype][stability][FB], 1, truncated=True)
                _, dose_test_transform_flat[dosetype][stability][FB] = transform_data(
                    dose_test[dosetype][stability][FB], 1, truncated=True)
                _, dose_fit_transform_flat[dosetype][stability][FB] = transform_data(
                    dose_fit[dosetype][stability][FB], 1, truncated=True)
                aam[dosetype][stability][FB] = {}
                score[dosetype][stability][FB] = {}
                krigeage[dosetype][stability][FB] = {}

                dimension = 9
                n_spline = [(4, 200)]
                rcond = 0.1
                topology = 'rank'
                th_reduction = 1.1

                ## AAM
                aamodel = AutoAssociativeModel(
                    data=dose_train_transform_flat[dosetype][stability][FB])
                aamodel.train(dimension=dimension, n_spline=n_spline,
                              rcond=rcond, topology=topology,
                              data_fit=dose_fit_transform_flat[dosetype][stability][FB])

                _, score[dosetype][stability][FB] = aamodel.project(
                    dose_train_transform_flat[dosetype][stability][FB])
                aam[dosetype][stability][FB] = aamodel

                ## Kriging
                input_kriging = ot.Sample(doe_normalized_train)
                covariance_model = ot.MaternModel([1.0] * doe_normalized_train.shape[1], 2.5)
                basis = ot.ConstantBasisFactory(doe_normalized_train.shape[1]).build()

                for ii in range(dimension):
                    output_kriging = ot.Sample([[di]
                                                for di in score[dosetype][stability][FB][:,ii]])
                    model = ot.KrigingAlgorithm(input_kriging, output_kriging,
                                                covariance_model, basis)
                    model.run()
                    metamodel = model.getResult().getMetaModel()
                    krigeage[dosetype][stability][FB][ii] = metamodel


    ## Exporting emulator data
    metamodel_path = os.path.join(output_path, 'emulations/')
    osen.makedir(metamodel_path)
    pickle.dump(dose_train, open(metamodel_path + 'dose_train.pickle', 'wb'))
    pickle.dump(dose_test, open(metamodel_path + 'dose_test.pickle', 'wb'))
    pickle.dump(dose_fit, open(metamodel_path + 'dose_fit.pickle', 'wb'))
    pickle.dump(aam, open(metamodel_path + 'aam.pickle', 'wb'))
    pickle.dump(score, open(metamodel_path + 'score.pickle', 'wb'))
    pickle.dump(scaler, open(metamodel_path + 'scaler_aam.pickle', 'wb'))
    pickle.dump(krigeage, open(metamodel_path + 'krigeage_aam.pickle', 'wb'))

    fin = time.time()
    print("Emulators created in %.02f minutes" %((fin-debut)/60))
