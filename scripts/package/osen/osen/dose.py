from dosecoef import dosecoef
import numpy as np
import netCDF4
from .utils import interpolation

def concatenate_string(list_character):
    string = b''
    for ll in list(list_character):
        string += ll
    return string.decode('utf-8')


def calculate_dose(ActivityInteg, DepositionInteg, IsoNameResult):

    TS2 = dosecoef.GlobalIsoCoef(IsoNameResult)

    debit_respiratoire = 5.2/(24*3600) # en m3/sS

    ####################################
    ## Calcul de dose efficace totale ##
    ####################################

    TimeType = "integ"
    doseCible = "1an"
    doseOrgane = "Efficace"

    dose_activity = np.zeros(ActivityInteg.shape[:-1])
    dose_deposition = np.zeros(DepositionInteg.shape[:-1])
    dose_inhalation = np.zeros(ActivityInteg.shape[:-1])

    for i_iso, name_iso in enumerate(IsoNameResult):

        dose_activity += ActivityInteg[:,:,:,i_iso] * \
            TS2.queryCoef(doseCible, "Panache", org=doseOrgane)[i_iso]

        dose_deposition += DepositionInteg[:,:,:,i_iso] * \
            TS2.queryCoef(doseCible, "Depot", org=doseOrgane)[i_iso]

        dose_inhalation += ActivityInteg[:,:,:,i_iso] * \
            TS2.queryCoef(doseCible, "Inhalation", org=doseOrgane)[i_iso]

    Dose_Efficace = dose_activity + dose_deposition + dose_inhalation * debit_respiratoire
    del dose_activity
    del dose_deposition
    del dose_inhalation

    ########################################
    ## Calcul de dose inhalation thyroide ##
    ########################################

    TimeType = "integ"
    doseCible = "1an"
    doseOrgane = "Thyroide"

    dose_activity = np.zeros(ActivityInteg.shape[:-1])

    for i_iso, name_iso in enumerate(IsoNameResult):

        dose_activity += ActivityInteg[:,:,:,i_iso] * \
            TS2.queryCoef(doseCible, "Inhalation", org=doseOrgane)[i_iso] * debit_respiratoire

    Dose_Inhalation = dose_activity
    del dose_activity

    return Dose_Efficace, Dose_Inhalation



def load_dose_result(file_name):

    data_case = netCDF4.Dataset(file_name, 'r')

    CoordX0 = np.array(data_case.variables['CoordX0'])[0]
    CoordY0 = np.array(data_case.variables['CoordY0'])[0]

    DepotIntegSec = np.array(data_case.variables['ResultDepotIntegSec0-0'][:,0,:,:,:])
    DepotIntegHumide = np.array(data_case.variables['ResultDepotIntegHumide0-0'][:,0,:,:,:])
    ActivityInteg = np.array(data_case.variables['ResultInteg0-0'][:,0,:,:,:])
    DepositionInteg = DepotIntegSec + DepotIntegHumide

    IsoNameResult = [concatenate_string(L) for L in
                     np.array(data_case.variables['IsoNameListSource0'])]

    Dose_Efficace, Dose_Inhalation = calculate_dose(ActivityInteg, DepositionInteg,
                                                    IsoNameResult)

    return CoordX0, CoordY0, Dose_Efficace, Dose_Inhalation



def distance(R, VALUE, th, norm=None, middle=9):
    """
    Calculate the value of the maximum distance above a certain threshold 'th' for the variable 'VALUE'.
    """
    if middle==None:
        middle = (R.shape[0]-1)/2

    rr = R[middle,:]
    value = VALUE[middle,:]

    # from scipy.interpolate import spline
    # xnew = np.linspace(rr.min(), rr.max(), 1000)
    # smooth = spline(rr, value, xnew)
    # plt.plot(xnew, smooth, '-b')
    # plt.plot(rr, value, '-r')

    if sum(value > th) > 0:
        ind_1 = np.where(value > th)[0][-1]
        ind_2 = ind_1 + 1

        ## Si ca depasse le domaine, distance = max
        if ind_1 == len(rr) - 1:
            return rr[-1]

        ## Si c'est dans le domaine, on interpolle
        else:
            x1 = rr[ind_1]
            x2 = rr[ind_2]
            y1 = value[ind_1]
            y2 = value[ind_2]

            if norm == "log":
                if y1 == 0:
                    log_y1 = -999
                else:
                    log_y1 = np.log10(y1)
                if y2 == 0:
                    log_y2 = -999
                else:
                    log_y2 = np.log10(y2)
                x_mean = interpolation(x1, x2, log_y1, log_y2, np.log10(th))

            else:
                x_mean = interpolation(x1, x2, y1, y2, th)

            if np.isnan(x_mean):
                x_mean = 0.0

            return x_mean


    ## Si aucune valeur depasse, distance = 0.
    else:
        return 0.


def largeur(R, THETA, VALUE, th, norm=None):
    """
    Calculate the value of the area's width above a certain threshold 'th' for the variable 'VALUE', in the grid polar coordinate 'R' and 'THETA'.
    """

    ## Si R=0 est dans le domaine, on le retire
    if sum(R[:,0]) == 0:
        R_ = R[:,1:]
        THETA_ = THETA[:,1:]
        VALUE_ = VALUE[:,1:]
    else:
        R_ = R
        THETA_ = THETA
        VALUE_ = VALUE

    theta_list = range(int(round(THETA.min())), int(round(THETA.max())) + 10, 10)

    ## Si on a des valeurs, on interpole les angles
    ## la ou la valeur est la plus grande
    if np.sum(VALUE_ > th) > 0:
        theta_1 = round(THETA_[VALUE_ > th].max())
        ind_1 = theta_list.index(theta_1)
        value_list_1 = VALUE_[ind_1,:]
        r_1 = value_list_1.argmax()

        if ind_1 >= 27.:
            angle_gauche = 270.

        else:
            angle_1 = theta_list[ind_1]
            angle_2 = theta_list[ind_1 + 1]
            value_1 = VALUE_[ind_1, r_1]
            value_2 = VALUE_[ind_1 + 1, r_1]

            if norm == "log":
                if value_1 == 0:
                    log_v1 = -999
                else:
                    log_v1 = np.log10(value_1)
                if value_2 == 0:
                    log_v2 = -999
                else:
                    log_v2 = np.log10(value_2)
                angle_gauche = interpolation(angle_1, angle_2, log_v1, log_v2, np.log10(th))
            else:
                angle_gauche = interpolation(angle_1, angle_2, value_1, value_2, th)

        largeur = abs(90. - angle_gauche) * 2
    else:
        largeur = 0.0

    if np.isnan(largeur):
        largeur = 0.0

    return largeur
