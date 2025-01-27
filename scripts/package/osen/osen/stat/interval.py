# -*- coding: utf-8 -*-
# Author: Sylvain Girard (girard@phimeca.com)
"""Interval estimation.
"""
#§
import scipy.stats
import numpy as np

def average(data, threshold):
    """Estimate an interval bracketing the parameter of a Bernoulli variable
    with the add4 method.

    Args:
       data (array): index indiviual along the first dimension.
       threshold (float).
       risk (float): value in [0, 1], probability that the interval does not
           contain the true value of the parameter.

    Returns:
        lower (float): lower bound.
        upper (float): upper bound.
    """

    average = (data > threshold).mean(axis=0)

    return average


def add4(data, threshold, risk):
    """Estimate an interval bracketing the parameter of a Bernoulli variable
    with the add4 method.

    Args:
       data (array): index indiviual along the first dimension.
       threshold (float).
       risk (float): value in [0, 1], probability that the interval does not
           contain the true value of the parameter.

    Returns:
        lower (float): lower bound.
        upper (float): upper bound.
    """

    exceed = data > threshold

    # Quantile 1-risk/2 of the gaussian distribution.
    quantile = scipy.stats.norm.ppf(1-risk/2, 0, 1)

    n_success = exceed.sum(0)
    sample_size = np.alen(exceed)

    # Sample proportion plus 2 successes and 2 failures.
    average_adjusted = (n_success + 2) / (sample_size + 4)
    # TODO: check these formulae.
    half_interval = quantile * np.sqrt(
        average_adjusted * (1 - average_adjusted)/(sample_size + 4))
    lower = average_adjusted - half_interval
    upper = average_adjusted + half_interval

    return lower, upper

def score(data, threshold, risk):
    """Estimate an interval bracketing the parameter of a Bernoulli variable
    with the Score method.

    Args:
       data (array): index indiviual along the first dimension.
       threshold (float).
       risk (float): value in [0, 1], probability that the interval does not
           contain the true value of the parameter.

    Returns:
        lower (float): lower bound.
        upper (float): upper bound.
    """
    exceed = data > threshold

    # Quantile 1-risk/2 of the gaussian distribution.
    quantile = scipy.stats.norm.ppf(1-risk/2, 0, 1)
    n_success = exceed.sum(0)
    sample_size = np.alen(exceed)
    mult = 1/(1 + quantile**2/sample_size)
    # The sample mean.
    average = n_success/sample_size

    # TODO: check these formulae.
    half_interval = quantile * np.sqrt(
        (average*(1-average) + (quantile**2/(4*sample_size)))/sample_size)
    lower = (average + quantile**2/(2*sample_size) - half_interval)*mult
    upper = (average + quantile**2/(2*sample_size) + half_interval)*mult
    
    return lower, upper

#§
def decide(threshold, lower, upper):
    """Create a decision variable based on the threshold and the confidence
    interval.

    Args:
        threshold (float).
        lower (float): lower bound of the confidence interval.
        upper (float): upper bound of the confidence interval.

    Returns:
        decision (array).
            0   : threshold is below the lower bound.
            0.5 : threshold is under the lower and the upper bound.
            1   : threshold is above the upper bound.

    """

    decision = (lower >= threshold)/2. + (upper >= threshold)/2.

    return decision

#§
