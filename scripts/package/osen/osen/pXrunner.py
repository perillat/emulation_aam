# -*- coding: utf-8 -*-

import os, sys, time, socket, subprocess
from .pxWriteParam import ParamGlobal
# from NetCDFManager import *
from NetCDFManager.source import *
from NetCDFManager.result import *
from NetCDFManager import utils


#############################
#### Chemins des données ####
#############################

PX_DIR = "/home/perillat/code/pX/px-2.4.1"
CONSX_DIR = "/home/perillat/code/consx/python36/build/scripts-3.7/consx"

###################################
#### Chargement des paramètres ####
###################################

def fillParam(meteo_file, source_file, domain_file, result_file,
              date_beg, date_end, sigma = "Doury", FB=1):
    """
    Ecrit les partie communes du fichier paramétrique.
    """
    pg = ParamGlobal()
    pg.setDateDeb(date_beg.strftime("%d/%m/%Y %H:%M"))
    pg.setDateFin(date_end.strftime("%d/%m/%Y %H:%M"))
    pg.loadPasDeTempsADR(10.)
    pg.loadCoefPasDeTempsApPuff(1)
    pg.loadCoefPasDeTempsFilPuff(2)
    pg.loadCoefPasDeTempsDepot(2)
    pg.loadCoefPasDeTempsInteg(2)
    pg.TauxReconstr(1.3)
    pg.loadSigType(sigma.upper())
    if sigma.lower() == "diff":
        pg.loadCoeffDiffH(200.)
        pg.loadCoeffDiffV(100.)
    pg.loadFactBat(FB)
    pg.setMeteoFile(meteo_file)
    pg.setSourceFile(source_file)
    pg.setResultFile(domain_file)
    pg.setResultFileOut(result_file)
    pg.CoefPasDeTempsReconstr(5)
    pg.loadFormuleGauss("APPROCHE")
    pg.loadSeuilGauss(4)
    return pg


##############################################################
#### Lancement automatique de pX avec les bons paramètres ####
##############################################################

def launch_px(data_path, meteo_file, source_file, domain_file,
              date_beg, date_end, sigma, FB, result_path,
              ref_file, family_file):

    # Chemin des données
    result_file = result_path + 'results.nc'

    # Création du fichier de param de px
    pg = fillParam(meteo_file, source_file, domain_file, result_file, date_beg, date_end, sigma, FB)
    param_file = os.path.join(result_path, "param")
    pg.loadRadioElementFile(ref_file)
    pg.loadFamillesFile(family_file)
    pg.writeParamFile(param_file)

    # Exécution de px
    hostname = socket.getfqdn().split('.')[0]
    pxExe = os.path.join(PX_DIR, "bin", "px")
    log_file = os.path.join(result_path, "log_px")

    # subprocess.call([pxExe, "--runmode", "RS",
    #                  "--def_param_file", os.path.join(PX_DIR, ".def_param"),
    #                  "--param_file", param_file, ">", log_file], shell=False)

    with open(log_file, "w") as f:
        subprocess.run([pxExe, "--runmode", "RS",
                        "--def_param_file", os.path.join(PX_DIR, ".def_param"),
                        "--param_file", param_file], stdout=f, text=True)


##########################
### Lancement de consx ###
##########################

def launch_consx(data_path, result_path, consx_file="consx.cfg"):

    fr = open(consx_file, "r")
    output_file = result_path + "results.nc"
    config_file = os.path.join(result_path, "consx.cfg")
    consx_result_file = os.path.join(result_path, "consx_results.nc")

    # Writing config file
    fw = open(config_file, "w")
    fw.write("# Nom du fichier de resultat pX (.nc pour NeCdf)=\n")
    fw.write("Fichier de resultat= " + output_file +"\n")
    fw.write("\n# Nom du fichier de sortie (.nc pour NetCdf)=\n")
    fw.write("Fichier de sortie= " + consx_result_file +"\n\n")

    for l in fr.readlines():
        fw.write(l)

    fw.close()
    fr.close()

    log_file = os.path.join(result_path, "log_consx")

    # launching consx
    cmdLine =  CONSX_DIR + " -d " + \
               config_file  + " > " + log_file
    os.system(cmdLine)

##########
## Main ##
##########

def LaunchOne(config_data):

    # Dates simulation
    date_beg = utils.string_to_datetime(config_data['Date_beg'])
    date_end = utils.string_to_datetime(config_data['Date_end'])

    # Données statiques
    data_path = config_data['Data_path']
    family_file = os.path.join(data_path, "familles.pxs")
    consx_file = config_data['Consx_file']
    ref_file = os.path.join(config_data['Result_path'], "Ref.pxs")

    sigma = config_data['Sigma']
    FB = config_data['FB']
    result_file = os.path.join(config_data['Result_path'], "results.nc")

    meteo_file = config_data['Meteo']
    source_file = config_data['Source']
    domain_file = config_data['Domain']
    result_path = config_data['Result_path']

    ###############################
    ## Lancement des simulations ##
    ###############################

    # debut = time.time()
    launch_px(data_path, meteo_file, source_file, domain_file,
              date_beg, date_end, sigma, FB,
              result_path, ref_file, family_file)
