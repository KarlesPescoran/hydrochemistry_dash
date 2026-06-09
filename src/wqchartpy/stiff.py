# -*- coding: utf-8 -*-
"""
Created on Wed Sep 15 16:38:48 2021

@author: Jing
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import matplotlib as mpl
from pylab import *
import re

from .ions import ions_WEIGHT, ions_CHARGE, ions_label


def replace_ions(expr_list, mapping):
    def replace_expr(expr):
        # separa en tokens (palabras y operadores)
        tokens = re.findall(r"[A-Za-z0-9_]+|[+\-*/()]", expr)
        
        # reemplaza si está en el diccionario
        tokens = [mapping.get(t, t) for t in tokens]
        
        return "".join(tokens)
    
    return [replace_expr(expr) for expr in expr_list]


# Define the plotting function
def get_meqL(df,
             unit='mg/L'):
    """Plot the Stiff diagram.
    
    Parameters
    ----------
    df : class:`pandas.DataFrame`
        Geochemical data to draw Gibbs diagram.
    unit : class:`string`
        The unit used in df. Currently only mg/L is supported. 
    figname : class:`string`
        A path or file name when saving the figure.
    figformat : class:`string`
        The file format, e.g. 'png', 'pdf', 'svg'
        
        
     References
    ----------
    .. [1] Stiff, H.A. 1951.
           The Interpretation of Chemical Water Analysis by Means of Patterns
           Journal of Petroleum Technology 3(10): 15-3
           https://doi.org/10.2118/951376-G
    """
    # Basic data check 
    # -------------------------------------------------------------------------
    # Determine if the required geochemical parameters are defined. 
    # if not {'Sample', 'Ca', 'Mg', 'Na', 'K', 'HCO3', 'Cl', 'SO4'}.issubset(df.columns):
    #     raise RuntimeError("""
    #     Stiff diagram uses geochemical parameters Ca, Mg, Na, K, HCO3, Cl, and SO4.
    #     Also, Sample is requied to save the Stiff diagram to disk for each sample.
    #     Confirm that these parameters are provided in the input file.""")
        
    # Determine if the provided unit is allowed
    ALLOWED_UNITS = ['mg/L', 'meq/L']
    if unit not in ALLOWED_UNITS:
        raise RuntimeError("""
        Currently only mg/L and meq/L are supported.
        Convert the unit manually if needed.""")
        
    # Convert unit if needed
    print("IONESSSSSSSSS")
    print(df.columns)
    ions = [col for col in df.columns 
            if col in ions_WEIGHT and
            col in ions_CHARGE and
            pd.api.types.is_numeric_dtype(df[col])]
    print(ions)
    if unit == 'mg/L':
        dat = df[ions]
        gmol = np.array([ions_WEIGHT[i] for i in ions])
        eqmol = np.array([ions_CHARGE[i] for i in ions])
        
        meqL = (dat / np.abs(gmol)) * np.abs(eqmol)
        
    elif unit == 'meq/L':
        meqL = df[ions]
    
    else:
        raise RuntimeError("""
        Currently only mg/L and meq/L are supported.
        Convert the unit if needed.""")
    print(meqL)
    return meqL

def get_data_raw_from_meqL(meqL):

    ions = [
        col for col in meqL.columns
        if col in ions_WEIGHT and col in ions_CHARGE
    ]

    gmol = np.array([ions_WEIGHT[i] for i in ions])
    eqmol = np.array([ions_CHARGE[i] for i in ions])

    dat_meq = meqL[ions]

    # inverso:
    # mg/L = (meqL / |eqmol|) * |gmol|
    mgL = (dat_meq / np.abs(eqmol)) * np.abs(gmol)

    data_raw = meqL.copy()
    data_raw[ions] = mgL

    return data_raw
    
def plot(df, 
         name,
         cations = ['Na + K', 'Ca', 'Mg'],
         anions = ['Cl', 'HCO3', 'SO4'],
         ax   = None,
         xlim = None,
         backcolor = "none",
         showlabel = True,
         linetype = '-',
         ):    
    
    cations_label = replace_ions(cations, ions_label)
    anions_label = replace_ions(anions, ions_label)
    cat1 = df.eval(cations[0]).values
    cat2 = df.eval(cations[1]).values
    cat3 = df.eval(cations[2]).values
    an1 = df.eval(anions[0]).values
    an2 = df.eval(anions[1]).values
    an3 = df.eval(anions[2]).values

    cat_max = np.nanmax(np.array(((cat1, cat2, cat3))))
    an_max = np.nanmax(np.array(((an1, an2, an3))))

    # Plot the Stiff diagrams for each sample
    # -------------------------------------------------------------------------
    
    Labels = []
    # plt.figure()
    if ax is None:
        fig = plt.figure()
        fig.patch.set_facecolor(backcolor)
        ax = fig.add_subplot(111)
    
    for i in range(len(df)):
        color = df.at[i, "Color"]
        linetype = df.at[i, "Marker"]
        try:
            x = [-cat1[i], -cat2[i], -cat3[i], 
                an3[i], an2[i], an1[i], -(cat1[i])]
            y = [3, 2, 1, 1, 2, 3, 3]
            
            ax.fill(x, y, facecolor=color, edgecolor='k', linestyle=linetype, linewidth=1.25)                
        except(ValueError):
                pass
        
    ax.plot([0, 0], [1, 3], 'k-.', linewidth=1.25)
    ax.plot([-0.5, 0.5], [2, 2], 'k-')

    # cat_max = np.nanmax(np.array(((meqL[:, 2] + meqL[:, 3]), meqL[:, 0], meqL[:, 1])))
    # an_max = np.nanmax(meqL[:, 4:])
    cmax = cat_max if cat_max > an_max else an_max
    
    ax.set_xlim([-cmax*1.5, cmax*1.5])
    if showlabel:
        ax.text(-cmax, 2.9, cations_label[0], fontsize=10, ha= 'right')
        ax.text(-cmax, 1.9, cations_label[1], fontsize=10, ha= 'right')
        ax.text(-cmax, 1.0, cations_label[2], fontsize=10, ha= 'right')

        ax.text(cmax, 2.9, anions_label[0], fontsize=10, ha= 'left')
        ax.text(cmax, 1.9, anions_label[1], fontsize=10, ha= 'left')
        ax.text(cmax, 1.0, anions_label[2], fontsize=10, ha= 'left')

    ax.spines['left'].set_color('None')
    ax.spines['right'].set_color('None')
    ax.spines['top'].set_color('None')
    # minorticks_off()
    ax.tick_params(which='major', direction='out', length=4, width=1.25)
    ax.tick_params(which='minor', direction='in', length=2, width=1.25)
    ax.spines['bottom'].set_linewidth(1.25)
    ax.spines['bottom'].set_color('k')
    #ylim(0.8, 3.2)
    ax.set_yticks([])
    ax.set_yticklabels([])
    #plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))

    if xlim is not None:
        ax.set_xlim(-xlim, xlim)
        cmax = xlim
    ticks = np.array([-cmax, -cmax/2, 0, cmax/2, cmax])
    if cmax < 0.2:
        tickla = [f'{tick:1.2f}' for tick in abs(ticks)]
    else:
        tickla = [f'{tick:1.1f}' for tick in abs(ticks)]
    ax.set_xticks(ticks)
    ax.set_xticklabels(tickla)
    labels = ax.get_xticklabels()
    [label.set_fontsize(8) for label in labels]
    ax.set_xlabel('meq/L', fontsize=10, weight='normal')
    ax.set_title("".join(str(s) for s in name), fontsize=12, weight='normal')
    ax.patch.set_facecolor(backcolor)


    return ax


def plot_old(df, 
         unit='mg/L', 
         figname='Stiff diagram', 
         figformat='jpg',
         sep = True):
    """Plot the Stiff diagram.
    
    Parameters
    ----------
    df : class:`pandas.DataFrame`
        Geochemical data to draw Gibbs diagram.
    unit : class:`string`
        The unit used in df. Currently only mg/L is supported. 
    figname : class:`string`
        A path or file name when saving the figure.
    figformat : class:`string`
        The file format, e.g. 'png', 'pdf', 'svg'
        
        
     References
    ----------
    .. [1] Stiff, H.A. 1951.
           The Interpretation of Chemical Water Analysis by Means of Patterns
           Journal of Petroleum Technology 3(10): 15-3
           https://doi.org/10.2118/951376-G
    """
    # Basic data check 
    # -------------------------------------------------------------------------
    # Determine if the required geochemical parameters are defined. 
    if not {'Sample', 'Ca', 'Mg', 'Na', 'K', 'HCO3', 'Cl', 'SO4'}.issubset(df.columns):
        raise RuntimeError("""
        Stiff diagram uses geochemical parameters Ca, Mg, Na, K, HCO3, Cl, and SO4.
        Also, Sample is requied to save the Stiff diagram to disk for each sample.
        Confirm that these parameters are provided in the input file.""")
        
    # Determine if the provided unit is allowed
    ALLOWED_UNITS = ['mg/L', 'meq/L']
    if unit not in ALLOWED_UNITS:
        raise RuntimeError("""
        Currently only mg/L and meq/L are supported.
        Convert the unit manually if needed.""")
        
    # Convert unit if needed
    if unit == 'mg/L':
        gmol = np.array([ions_WEIGHT['Ca'], 
                         ions_WEIGHT['Mg'], 
                         ions_WEIGHT['Na'], 
                         ions_WEIGHT['K'], 
                         ions_WEIGHT['HCO3'],
                         ions_WEIGHT['Cl'], 
                         ions_WEIGHT['SO4']])
    
        eqmol = np.array([ions_CHARGE['Ca'], 
                          ions_CHARGE['Mg'], 
                          ions_CHARGE['Na'], 
                          ions_CHARGE['K'], 
                          ions_CHARGE['HCO3'],  
                          ions_CHARGE['Cl'], 
                          ions_CHARGE['SO4']])
    
        tmpdf = df[['Ca', 'Mg', 'Na', 'K', 'HCO3', 'Cl', 'SO4']]
        dat = tmpdf.values
        
        meqL = (dat / abs(gmol)) * abs(eqmol)
        
    elif unit == 'meq/L':
        meqL = df[['Ca', 'Mg', 'Na', 'K', 'HCO3', 'Cl', 'SO4']].values
    
    else:
        raise RuntimeError("""
        Currently only mg/L and meq/L are supported.
        Convert the unit if needed.""")
   
    cat_max = np.nanmax(np.array(((meqL[:, 2] + meqL[:, 3]), meqL[:, 0], meqL[:, 1])))
    an_max = np.nanmax(meqL[:, 4:])
    
    # Plot the Stiff diagrams for each sample
    # -------------------------------------------------------------------------
    
    Labels = []
    if sep:
        for i in range(len(df)):
            if (df.at[i, 'Label'] in Labels or df.at[i, 'Label'] == ''):
                TmpLabel = ''
            else:
                TmpLabel = df.at[i, 'Label']
                Labels.append(TmpLabel)
        
            try:
                x = [-(meqL[i, 2] + meqL[i, 3]), -meqL[i, 0], -meqL[i, 1], 
                                    meqL[i, 6], meqL[i, 4], meqL[i, 5], -(meqL[i, 2] + meqL[i, 3])]
                y = [3, 2, 1, 1, 2, 3, 3]

                plt.figure()
                plt.fill(x, y, facecolor='w', edgecolor='k', linewidth=1.25, alpha = 0.5)

                plt.plot([0, 0], [1, 3], 'k-.', linewidth=1.25)
                plt.plot([-0.5, 0.5], [2, 2], 'k-')

                # cat_max = np.nanmax(np.array(((meqL[:, 2] + meqL[:, 3]), meqL[:, 0], meqL[:, 1])))
                # an_max = np.nanmax(meqL[:, 4:])
                cmax = cat_max if cat_max > an_max else an_max
                print(cmax, an_max, cmax)
                plt.xlim([-cmax*1.5, cmax*1.5])
                plt.text(-cmax, 2.9, 'Na$^+$' + '+' + 'K$^+$', fontsize=12, ha= 'right')
                plt.text(-cmax, 1.9, 'Ca$^{2+}$', fontsize=12, ha= 'right')
                plt.text(-cmax, 1.0, 'Mg$^{2+}$', fontsize=12, ha= 'right')

                plt.text(cmax, 2.9,'Cl$^-$',fontsize=12, ha= 'left')
                plt.text(cmax, 1.9,'HCO'+'$_{3}^-$',fontsize=12,ha= 'left')
                plt.text(cmax, 1.0,'SO'+'$_{4}^{2-}$',fontsize=12,ha= 'left')

                ax = plt.gca()
                ax.spines['left'].set_color('None')
                ax.spines['right'].set_color('None')
                ax.spines['top'].set_color('None')
                minorticks_off()
                tick_params(which='major', direction='out', length=4, width=1.25)
                tick_params(which='minor', direction='in', length=2, width=1.25)
                ax.spines['bottom'].set_linewidth(1.25)
                ax.spines['bottom'].set_color('k')
                #ylim(0.8, 3.2)
                setp(gca(), yticks=[], yticklabels=[])
                #plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
                ticks = np.array([-cmax, -cmax/2, 0, cmax/2, cmax])
                tickla = [f'{tick:1.1f}' for tick in abs(ticks)]

                ax.xaxis.set_ticks(ticks)
                ax.xaxis.set_ticklabels(tickla)
                labels = ax.get_xticklabels()
                [label.set_fontsize(10) for label in labels]
                ax.set_xlabel('Stiff diagram (meq/L)', fontsize=12, weight='normal')
                    
                ax.set_title(df.at[i, 'Sample'], fontsize=14, weight='normal')

            except(ValueError):
                    pass
        
            # Display the info
            # cwd = os.getcwd()
            # print("Stiff plot created for %s. Saving it to %s\n" %(str(df.at[i, 'Sample']), cwd))
        
            # # Save the figure
            # plt.savefig(figname + '_' + str(df.at[i, 'Sample']) + '.' + figformat, format=figformat, 
            #             bbox_inches='tight', dpi=300)
            # return
    else:
        plt.figure()
        for i in range(len(df)):
            if (df.at[i, 'Label'] in Labels or df.at[i, 'Label'] == ''):
                TmpLabel = ''
            else:
                TmpLabel = df.at[i, 'Label']
                Labels.append(TmpLabel)
        
            try:
                x = [-(meqL[i, 2] + meqL[i, 3]), -meqL[i, 0], -meqL[i, 1], 
                    meqL[i, 6], meqL[i, 4], meqL[i, 5], -(meqL[i, 2] + meqL[i, 3])]
                y = [3, 2, 1, 1, 2, 3, 3]
                
                plt.fill(x, y, facecolor='w', edgecolor='k', linewidth=1.25, alpha = 0.5)

                plt.plot([0, 0], [1, 3], 'k-.', linewidth=1.25)
                plt.plot([-0.5, 0.5], [2, 2], 'k-')

                # cat_max = np.nanmax(np.array(((meqL[:, 2] + meqL[:, 3]), meqL[:, 0], meqL[:, 1])))
                # an_max = np.nanmax(meqL[:, 4:])
                cmax = cat_max if cat_max > an_max else an_max

                plt.xlim([-cmax*1.5, cmax*1.5])
                plt.text(-cmax, 2.9, 'Na$^+$' + '+' + 'K$^+$', fontsize=12, ha= 'right')
                plt.text(-cmax, 1.9, 'Ca$^{2+}$', fontsize=12, ha= 'right')
                plt.text(-cmax, 1.0, 'Mg$^{2+}$', fontsize=12, ha= 'right')

                plt.text(cmax, 2.9,'Cl$^-$',fontsize=12, ha= 'left')
                plt.text(cmax, 1.9,'HCO'+'$_{3}^-$',fontsize=12,ha= 'left')
                plt.text(cmax, 1.0,'SO'+'$_{4}^{2-}$',fontsize=12,ha= 'left')

                ax = plt.gca()
                ax.spines['left'].set_color('None')
                ax.spines['right'].set_color('None')
                ax.spines['top'].set_color('None')
                minorticks_off()
                tick_params(which='major', direction='out', length=4, width=1.25)
                tick_params(which='minor', direction='in', length=2, width=1.25)
                ax.spines['bottom'].set_linewidth(1.25)
                ax.spines['bottom'].set_color('k')
                #ylim(0.8, 3.2)
                setp(gca(), yticks=[], yticklabels=[])
                #plt.gca().xaxis.set_major_locator(MaxNLocator(integer=True))
                ticks = np.array([-cmax, -cmax/2, 0, cmax/2, cmax])
                tickla = [f'{tick:1.1f}' for tick in abs(ticks)]

                ax.xaxis.set_ticks(ticks)
                ax.xaxis.set_ticklabels(tickla)
                labels = ax.get_xticklabels()
                [label.set_fontsize(10) for label in labels]
                ax.set_xlabel('Stiff diagram (meq/L)', fontsize=12, weight='normal')
                    
                ax.set_title(df.at[i, 'Sample'], fontsize=14, weight='normal')

            except(ValueError):
                    pass
        
            # Display the info
            # cwd = os.getcwd()
            # print("Stiff plot created for %s. Saving it to %s\n" %(str(df.at[i, 'Sample']), cwd))
        
            # Save the figure
            # plt.savefig(figname + '_' + str(df.at[i, 'Sample']) + '.' + figformat, format=figformat, 
            #             bbox_inches='tight', dpi=300)
    return
    
    
        
    

# if __name__ == '__main__':
#     # Example data
#     data = {'Sample' : ['sample1', 'sample2', 'sample3', 'sample4', 'sample5', 'sample6'],
#             'Label'  : ['C1', 'C2', 'C2', 'C3', 'C3', 'C1'],
#             'Color'  : ['red', 'green', 'green', 'blue', 'blue', 'red'],
#             'Marker' : ['o', 'o', 'o', 'o', 'o', 'o'],
#             'Size'   : [30, 30, 30, 30, 30, 30],
#             'Alpha'  : [0.6, 0.6, 0.6, 0.6, 0.6, 0.6],
#             'pH'     : [7.8, 7.6, 7.5, 7.7, 7.4, 7.1],
#             'Ca'     : [32, 46, 54, 50, 50, 134],
#             'Mg'     : [6, 11, 11, 11, 22, 21],
#             'Na'     : [28, 17, 16, 25, 25, 39],
#             'K'      : [2.8, 0.7, 2.4, 2.8, 0.5, 6.4],
#             'HCO3'   : [73, 201, 207, 244, 305, 275],
#             'CO3'    : [0, 0, 0, 0, 0, 0],
#             'Cl'     : [43, 14, 18, 18, 11, 96],
#             'SO4'    : [48, 9, 10, 9, 9, 100],
#             'TDS'    : [233, 299, 377, 360, 424, 673],
#             }
#     df = pd.DataFrame(data)
#     # df = pd.read_csv('../data/data_template.csv')
#     plot(df, unit='mg/L', figname='Stiff diagram', figformat='jpg')
    
    
    
    