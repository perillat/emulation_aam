import NetCDFManager
import datetime
import numpy as np
import pickle, os
import openturns as ot
from itertools import product
import csv


def makedir(path):
    if os.path.exists(path) == False:
        os.makedirs(path)


def write_doe(sample, variable_list, dir_out, file_name):
    makedir(dir_out)
    file_path = os.path.join(dir_out, file_name + '.txt')

    with open(file_path, 'w') as f:
        variable_names = variable_list
        f.write('\t'.join(variable_names) + '\n')

        for values in sample:
            line = '\t'.join(str(value) for value in values)
            f.write(line + '\n')



def read_doe(file_path):
    data = []
    with open(file_path, 'r') as f:
        reader = csv.reader(f, delimiter='\t')
        variable_names = next(reader)
        for row in reader:
            converted_row = [float(value) for value in row]
            data.append(converted_row)
    return variable_names, np.array(data)


# Le plan d'expérience d'entrainement est une séquence de Sobol'
# pour pouvoir couvrir uniformément tout l'espace des entrées,
# tout en laissant la possibilité de rajouter des points facilement
# si on a besoin de densifier le tirage.

def create_doe_train(doe_path, variable_list, min_list, max_list, transform,
                     sample_size=1024, seed=29081920, name=None):

    variable_list_ = variable_list.copy()
    min_list_ = min_list.copy()
    max_list_ = max_list.copy()
    transform_ = transform.copy()

    ot.RandomGenerator.SetSeed(seed)

    # On retire "Amplitude" de la liste
    if "Amplitude" in variable_list_:
        idx = variable_list_.index("Amplitude")
        variable_list_.pop(idx)
        min_list_.pop(idx)
        max_list_.pop(idx)
        transform_.pop(idx)

    # Nombre de variables à considérer dans le DOE
    n_dim = len(variable_list_)

    # Créer une liste qui contient les bornes des entrées
    list_bound = []
    for ii in range(n_dim):
        if transform_[ii] == "Log":
            list_bound.append([np.log(min_list_[ii]), np.log(max_list_[ii])])
        else:
            list_bound.append([min_list_[ii], max_list_[ii]])

    # Créer une liste de distributions uniformes pour chaque variable
    uniform_distributions = [ot.Uniform(bound[0], bound[1]) for bound in list_bound]

    # Créer une distribution multivariée à partir des distributions uniformes
    distribution = ot.ComposedDistribution(uniform_distributions)

    # Créer un échantillonneur de plan d'expérience avec un LHS
    sobol_sampler = ot.SobolSequence(n_dim)

    # Générer les échantillons avec LHS
    sobol_sample = sobol_sampler.generate(sample_size)

    # Appliquer les bornes aux valeurs de la séquence de Sobol
    for i in range(n_dim):
        sobol_sample[:, i] *= (list_bound[i][1] - list_bound[i][0])
        sobol_sample[:, i] += list_bound[i][0]

    if name==None:
        file_name = 'DOE_test'
    else:
        file_name = name
    write_doe(sobol_sample, variable_list_, doe_path, file_name)

    return sobol_sample



# Le plan d'expérience de test est un LHS sur l'espace des entrées
# pour pouvoir couvrir uniformément tout l'espace des entrées.

def create_doe_test(doe_path, variable_list, min_list, max_list, transform,
                    sample_size=500, seed=1, name=None):

    variable_list_ = variable_list.copy()
    min_list_ = min_list.copy()
    max_list_ = max_list.copy()
    transform_ = transform.copy()

    ot.RandomGenerator.SetSeed(seed)

    # On retire "Amplitude" de la liste
    if "Amplitude" in variable_list_:
        idx = variable_list_.index("Amplitude")
        variable_list_.pop(idx)
        min_list_.pop(idx)
        max_list_.pop(idx)
        transform_.pop(idx)

    # Nombre de variables à considérer dans le DOE
    n_dim = len(variable_list_)

    # Créer une liste qui contient les bornes des entrées
    list_bound = []
    for ii in range(n_dim):
        if transform_[ii] == "Log":
            list_bound.append([np.log(min_list_[ii]), np.log(max_list_[ii])])
        else:
            list_bound.append([min_list_[ii], max_list_[ii]])


    # Créer une liste de distributions uniformes pour chaque variable
    uniform_distributions = [ot.Uniform(bound[0], bound[1]) for bound in list_bound]

    # Créer une distribution multivariée à partir des distributions uniformes
    distribution = ot.ComposedDistribution(uniform_distributions)

    # Créer un échantillonneur de plan d'expérience avec un LHS
    lhs_sampler = ot.LHSExperiment(distribution, sample_size)

    # Générer les échantillons avec LHS
    lhs_sample = lhs_sampler.generate()

    if name==None:
        file_name = 'DOE_test'
    else:
        file_name = name
    write_doe(lhs_sample, variable_list_, doe_path, file_name)

    return lhs_sample


def create_double_amplitude(N_simulation, maxi=100., mini=10., seed=0):

    np.random.seed(seed=seed)

    ## On génère un nombre aléatoire
    rand = np.random.rand(N_simulation)

    ## On prend le nombre qui est à 0.5 de distance
    rand2 = (rand + 0.5) % 1.

    ## On initialise les amplitudes aléatoires
    Amplitude = np.zeros((N_simulation, 2))

    ## On utilise les nombres aléatoires pour générer l'amplitude
    Amplitude[:,0] = (maxi-mini) * rand + mini
    Amplitude[:,1] = (maxi-mini) * rand2 + mini

    return Amplitude


def create_ref_file(path_file_in, path_file_out, Vd, Vdi, As):

    file_in = open(path_file_in, 'r')
    file_out = open(path_file_out, 'w')
    lines = file_in.readlines()
    for line in lines:
        line = line.replace('%vdiode', '%1.2e' % Vdi)
        line = line.replace('%vd', '%1.2e' % Vd)
        line = line.replace('%scav', '%1.2e' % As)
        file_out.write(line)
    file_in.close()
    file_out.close()


def create_homogeneous_meteo(output_file, Wind=7., Rain=2., HCLA=1000., Stability = 3.,
                             date_init='12/04/2020 08:00:00', duration=72):
    """
    Crée une météo homogène et l'écrit dans un fichier NetCDF.

    Args:
        output_file (str): Chemin du fichier de sortie NetCDF.
        Wind (float, optional): Vitesse du vent en m/s. Par défaut, 7.0.
        Rain (float, optional): Précipitations en mm/h. Par défaut, 2.0.
        HCLA (float, optional): Hauteur de couche limite atmosphérique en mètres. Par défaut, 1000.0.
        Stability (float, optional): Stabilité atmosphérique. Par défaut, 3.0.
        date_init (str, optional): Date et heure initiale au format 'jour/mois/année heure:minute:seconde'.
            Par défaut, '12/04/2020 08:00:00'.
        duration (int, optional): Durée totale en heures. Par défaut, 72.

    Returns:
        None
    """

    date_beg = datetime.datetime.strptime(date_init, "%d/%m/%Y %H:%M:00")
    date_end = date_beg + datetime.timedelta(hours=duration)

    meteo = NetCDFManager.Meteo()
    meteo.createPointSet1D(150000, 150000, [0, 4000])
    meteo.setTimeRef(date_beg)
    meteo.setDate(date_beg, date_end, duration*3600.)

    rain = np.ones((2,2,2)) * Rain
    hcla = np.ones((2,2,2)) * HCLA
    stab = np.ones((2,2,2)) * Stability
    windu = np.ones((2,2,2,2)) * 0.
    windv = np.ones((2,2,2,2)) * Wind
    windw = np.ones((2,2,2,2)) * 0

    met_param = {'Rain': rain,
                 'VitU': windu,
                 'VitV': windv,
                 'VitW': windw,
                 'Stab': stab,
                 'HCLA': hcla,}

    meteo.fillMeteoField(met_param)

    met_param = {'Rain': rain,
                 'VitU': windu,
                 'VitV': windv,
                 'VitW': windw,
                 'Stab': stab,
                 'HCLA': hcla,}

    for var in met_param.keys():
        meteo.variables[var] = met_param[var]

    meteo.globalAttr['Meteo_long_name'] = "meteo"

    meteo.writeNC(output_file)


def create_sourceterm(input_file, ref_file, output_file, Height=0., MltFactor=1.,
                      date_init='12/04/2020 08:00:00', duration=72):
    """
    Crée un terme source au format NetCDF à partir d'un fichier d'entrée en CSV et d'un fichier de référence.

    Args:
        input_file (str): Chemin du fichier d'entrée contenant les données du terme source au format CSV.
        ref_file (str): Chemin du fichier de référence contenant les informations de correspondance avec les noms des isotopes.
        output_file (str): Chemin du fichier de sortie NetCDF.
        Height (float, optional): Hauteur du terme source. Par défaut, 0.0.
        MltFactor (float, optional): Facteur de multiplication appliqué aux données du terme source. Par défaut, 1.0.
        date_init (str, optional): Date et heure initiale au format 'jour/mois/année heure:minute:seconde'.
            Par défaut, '12/04/2020 08:00:00'.
        duration (int, optional): Durée totale en heures. Par défaut, 72.

    Returns:
        None
    """

    date_beg = datetime.datetime.strptime(date_init, "%d/%m/%Y %H:%M:00")
    date_end = date_beg + datetime.timedelta(hours=duration)

    # INFOS DU TS .CSV
    f = open(input_file)
    lines = f.readlines()
    f.close()

    IsoNameListSource1 = lines[8].replace('\r', '').replace('\n','').split(';')[1:]
    TimeSource1 = [0] + [float(line.split(';')[0]) for line in lines[10:154]]
    DateList1 = [date_beg + datetime.timedelta(0,tt) for tt in TimeSource1]
    source_data_cumul1 = np.array([[float(col.replace('\n',''))
                                    for col in line.split(';')[1:]]
                                   for line in lines[10:154]])
    source_data_cumul_1 = np.zeros((source_data_cumul1.shape[0]+1, source_data_cumul1.shape[1]))
    source_data_cumul_1[1:,:] = source_data_cumul1[:,:]
    source_data1 = np.diff(source_data_cumul_1, axis=0)/(60.*10)

    IsoNameListSource2 = lines[157].replace('\r', '').replace('\n','').split(';')[1:]
    TimeSource2 = [0] + [float(line.split(';')[0]) for line in lines[159:-1]]
    DateList2 = [date_beg + datetime.timedelta(0,tt) for tt in TimeSource2]
    source_data_cumul2 = np.array([[float(col.replace('\n',''))
                                    for col in line.split(';')[1:]]
                                   for line in lines[159:-1]])
    source_data_cumul_2 = np.zeros((source_data_cumul2.shape[0]+1, source_data_cumul2.shape[1]))
    source_data_cumul_2[1:,:] = source_data_cumul2[:,:]
    source_data2 = np.diff(source_data_cumul_2, axis=0)/(60.*10)

    source_data = source_data1 + source_data2

    # INFOS DU REF.PXS
    f = open(ref_file)
    lines = f.readlines()
    name_ref = [line.split('\t')[1] for line in lines[2:]]
    id_ref = [float(line.split('\t')[0]) for line in lines[2:]]
    f.close()
    id_dict = {}
    for ii in range(len(id_ref)):
        id_dict[name_ref[ii]] = id_ref[ii]

    # ECRITURE EN NETCDF
    source = NetCDFManager.Source()
    source.setSourceHeight(Height)
    source.setTimeRef(date_beg)
    IsoNameListSource0 = []
    IsoIdListSource0 = []
    index_iso = []
    for i_iso, iso in enumerate(IsoNameListSource1):
        if iso in name_ref:
            if sum(source_data[:, IsoNameListSource1.index(iso)]) > 0:
                IsoNameListSource0.append(iso)
                IsoIdListSource0.append(id_dict[iso])
                index_iso.append(i_iso)

    source.addSource(DateList1, IsoNameListSource0, IsoIdListSource0, MltFactor * source_data[:,index_iso], 0)
    source.createPointSet([[[0]]], [[[0]]], [[[Height]]], name_list=['Centre'], index=0)
    source.writeNC(output_file)


def create_circular_domain(output_file, xc=0, yc=0, zc=0, n_theta=36, delta_t=3600, date_init='12/04/2020 08:00:00', duration=24, r_list=None, coord_file=None):

    """
    Crée un domaine circulaire dans un fichier NetCDF.

    Args:
        output_file (str): Chemin du fichier de sortie NetCDF.
        xc (float, optional): Coordonnée x du centre du cercle. Par défaut, 0.
        yc (float, optional): Coordonnée y du centre du cercle. Par défaut, 0.
        zc (float, optional): Coordonnée z du centre du cercle. Par défaut, 0.
        n_theta (int, optional): Nombre de divisions angulaires. Par défaut, 36.
        delta_t (float, optional): Intervalle de temps en secondes. Par défaut, 3600.
        date_init (str, optional): Date et heure initiale au format 'jour/mois/année heure:minute:seconde'.
            Par défaut, '12/04/2020 08:00:00'.
        duration (int, optional): Durée totale en heures. Par défaut, 72.
        r_list (list, optional): Liste des rayons du cercle. Si non spécifié, une liste de rayons prédéfinis sera utilisée.
            Par défaut, None.
        coord_file (str, optional): Répertoire de sauvegarde des coordonnées au format npy
            Par défaut, None.

    Returns:
        None
    """

    date_beg = datetime.datetime.strptime(date_init, "%d/%m/%Y %H:%M:00")
    date_end = date_beg + datetime.timedelta(hours=duration)

    delta_angle_deg = 360/n_theta

    if r_list == None:
        r_list = [0, 500, 750, 1000, 1500, 2000, 2500, 3000, 3500, 4000,
                  4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000, 8500,
                  9000, 9500, 10000, 10500, 11000, 11500, 12000, 12500,
                  13000, 13500, 14000, 14500, 15000, 15500, 16000, 16500,
                  17000, 17500, 18000, 18500, 19000, 19500, 20000, 20500,
                  21000, 21500, 22000, 22500, 23000, 23500, 24000, 24500,
                  25000, 25500, 26000, 26500, 27000, 27500, 28000, 28500,
                  29000, 29500, 30000]

    angle_min = 0
    angle_max = 360

    zlist = [0]
    result_type = 4
    pi = np.pi

    Nr = len(r_list)
    Nangle = int((angle_max-angle_min) / delta_angle_deg)
    Nz = max(1, len(zlist))

    x = np.zeros((Nz, Nangle, Nr),'d')
    y = np.zeros((Nz, Nangle, Nr),'d')
    z = np.zeros((Nz, Nangle, Nr),'d')
    for i, r in enumerate(r_list):
        xmin = r*np.cos(2*pi*angle_min / 360.)
        ymin = r*np.sin(2*pi*angle_min / 360.)
        alpha_list = [angle_min + j*delta_angle_deg for j in range(Nangle)]
        xlist = np.array([r*np.cos(2*pi*alpha / 360.) for alpha in alpha_list])
        ylist = np.array([r*np.sin(2*pi*alpha / 360.) for alpha in alpha_list])
        for j in range(Nangle):
            for k in range(Nz):
                x[k,j,i] = xc + xlist[j]
                y[k,j,i] = yc + ylist[j]
                z[k,j,i] = zc + zlist[k]

    NetCDFManager.domain.createDomain(output_file, x, y, z,
                                      date_beg, date_end, delta_t, result_type)

    if coord_file != None:
        np.save(os.path.join(coord_file, 'CoordX.npy'), np.squeeze(x))
        np.save(os.path.join(coord_file, 'CoordY.npy'), np.squeeze(y))
