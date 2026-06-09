# -*- coding: utf-8 -*-
"""
Created on Thu Sep 16 11:51:24 2021

@author: Jing
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math

from .ions import ions_WEIGHT, ions_CHARGE

# Define the plotting function
def plot(df, 
         unit='mg/L', 
         figname='rectangle Piper diagram', 
         figformat='jpg',
         ax=None):
    """Plot the rectangular Piper diagram.
    
    Parameters
    ----------
    df : class:`pandas.DataFrame`
        Geochemical data to draw Gibbs diagram.
    unit : class:`string`
        The unit used in df. Currently only mg/L and meq/L are supported. 
    figname : class:`string`
        A path or file name when saving the figure.
    figformat : class:`string`
        The figure format to be saved, e.g. 'png', 'pdf', 'svg'
    ax : matplotlib.axes.Axes, optional
        The axes to plot on. If None, a new figure is created.
        
        
    References
    ----------
    .. [1] Piper, A.M. 1944.
           A Graphic Procedure in the Geochemical Interpretation of 
           Water-Analyses. Eos, Transactions American Geophysical 
           Union, 25, 914-928.
           http://dx.doi.org/10.1029/TR025i006p00914
    """
    # Basic data check 
    # -------------------------------------------------------------------------
    # Determine if the required geochemical parameters are defined. 
    if not {'Ca', 'Mg', 'Na', 'K', 
            'HCO3', 'CO3', 'Cl', 'SO4'}.issubset(df.columns):
        raise RuntimeError("""
        Trilinear Piper diagram requires geochemical parameters:
        Ca, Mg, Na, K, HCO3, CO3, Cl, and SO4.
        Confirm that these parameters are provided in the input file.""")
        
    # Determine if the provided unit is allowed
    ALLOWED_UNITS = ['mg/L', 'meq/L']
    if unit not in ALLOWED_UNITS:
        raise RuntimeError("""
        Currently only mg/L and meq/L are supported.
        Convert the unit manually if needed.""")
        
    # Global plot settings
    # -------------------------------------------------------------------------
    # Change default settings for figures
    plt.style.use('default')
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.labelsize'] = 10
    plt.rcParams['axes.labelweight'] = 'bold'
    plt.rcParams['axes.titlesize'] = 10
    plt.rcParams['xtick.labelsize'] = 10
    plt.rcParams['ytick.labelsize'] = 10
    plt.rcParams['legend.fontsize'] = 10
    plt.rcParams['figure.titlesize'] = 10   
    
    # Plot background settings
    # -------------------------------------------------------------------------
    xmin = 0
    xmax = 100
    ymin = 0
    ymax = 100
    
    if ax is None:
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, aspect='equal')
    else:
        ax.set_aspect('equal')

    ax.plot([xmin, xmax, xmax, xmin, xmin], [ymin, ymin, ymax, ymax, ymin],
             linestyle='-', linewidth=1.5, color='k')
    
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    
    # The axis lines in the center
    ax.plot([xmin, xmax], [50, 50], linestyle='-', linewidth=1.0, color='k')
    ax.plot([50, 50], [ymin, ymax], linestyle='-', linewidth=1.0, color='k')
    
    # Labels
    ax.text(50, -10, '$Na^++K^+$' + ' (%)', ha='center', va='center', fontsize=12)
    ax.text(-12, 50, '$SO_4^{2-}+Cl^-$' + ' (%)', ha='center', va='center', fontsize=12, rotation=90)
    
    # Mark the subfileds
    ax.text(25, 75, '1', fontsize=26, color="0.8", ha='center', va='center')
    ax.text(75, 75, '2', fontsize=26, color="0.8", ha='center', va='center')
    ax.text(25, 25, '3', fontsize=26, color="0.8", ha='center', va='center')
    ax.text(75, 25, '4', fontsize=26, color="0.8", ha='center', va='center')
    
    # Convert unit if needed
    if unit == 'mg/L':
        gmol = np.array([ions_WEIGHT['Ca'], 
                         ions_WEIGHT['Mg'], 
                         ions_WEIGHT['Na'], 
                         ions_WEIGHT['K'], 
                         ions_WEIGHT['HCO3'],
                         ions_WEIGHT['CO3'], 
                         ions_WEIGHT['Cl'], 
                         ions_WEIGHT['SO4']])
    
        eqmol = np.array([ions_CHARGE['Ca'], 
                          ions_CHARGE['Mg'], 
                          ions_CHARGE['Na'], 
                          ions_CHARGE['K'], 
                          ions_CHARGE['HCO3'], 
                          ions_CHARGE['CO3'], 
                          ions_CHARGE['Cl'], 
                          ions_CHARGE['SO4']])
    
        tmpdf = df[['Ca', 'Mg', 'Na', 'K', 'HCO3', 'CO3', 'Cl', 'SO4']]
        dat = tmpdf.values
        
        meqL = (dat / abs(gmol)) * abs(eqmol)
        
    elif unit == 'meq/L':
        meqL = df[['Ca', 'Mg', 'Na', 'K', 'HCO3', 'CO3', 'Cl', 'SO4']].values
    
    else:
        raise RuntimeError("""
        Currently only mg/L and meq/L are supported.
        Convert the unit if needed.""")
    
    # Calculate the percentages
    sumcat = np.sum(meqL[:, 0:4], axis=1)
    suman = np.sum(meqL[:, 4:8], axis=1)
    cat = np.zeros((dat.shape[0], 3))
    an = np.zeros((dat.shape[0], 3))
    cat[:, 0] = meqL[:, 0] / sumcat                  # Ca
    cat[:, 1] = meqL[:, 1] / sumcat                  # Mg
    cat[:, 2] = (meqL[:, 2] + meqL[:, 3]) / sumcat   # Na+K
    an[:, 0] = (meqL[:, 4] + meqL[:, 5]) / suman     # HCO3 + CO3
    an[:, 2] = meqL[:, 6] / suman                    # Cl
    an[:, 1] = meqL[:, 7] / suman                    # SO4
    
    # Plot the scatter
    Labels = []
    cf = None
    for i in range(len(df)):
        if (df.at[i, 'Label'] in Labels or df.at[i, 'Label'] == ''):
            TmpLabel = ''
        else:
            TmpLabel = df.at[i, 'Label']
            Labels.append(TmpLabel)
    
        try:
            if (df['Color'].dtype is np.dtype('float')) or \
                (df['Color'].dtype is np.dtype('int64')):
                vmin = np.min(df['Color'].values)
                vmax = np.max(df['Color'].values)
                cf = ax.scatter(100 * cat[i, 2], 100 * (an[i, 1] + an[i, 2]), 
                                marker=df.at[i, 'Marker'],
                                s=df.at[i, 'Size'], 
                                c=df.at[i, 'Color'], vmin=vmin, vmax=vmax,
                                alpha=df.at[i, 'Alpha'],
                                label=TmpLabel, 
                                edgecolors='black') 
            
            else:
                ax.scatter(100 * cat[i, 2], 100 * (an[i, 1] + an[i, 2]), 
                       marker=df.at[i, 'Marker'],
                       s=df.at[i, 'Size'], 
                       color=df.at[i, 'Color'], 
                       alpha=df.at[i, 'Alpha'],
                       label=TmpLabel, 
                       edgecolors='black') 
        except(ValueError):
            pass
            
    # Creat the legend
    if (df['Color'].dtype is np.dtype('float')) or (df['Color'].dtype is np.dtype('int64')):
        if cf is not None:
            cb = plt.colorbar(cf, ax=ax, extend='both', spacing='uniform',
                              orientation='vertical', fraction=0.025, pad=0.05)
            cb.ax.set_ylabel('$TDS$' + ' ' + '$(mg/L)$', rotation=90, labelpad=-55, fontsize=14)
    
    n_legend = math.ceil(len(set(df['Label'])) / 16)
    ax.legend(
        loc='upper left', 
        bbox_to_anchor=(0.075, 0.925), 
        ncol = n_legend,
        frameon=False,
        fontsize=10
    )
    
    return ax
