# -*- coding: utf-8 -*-
"""
Created on Fri Sep 17 14:33:20 2021

@author: Jing
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pylab import *

from .ions import ions_WEIGHT, ions_CHARGE, ions_label
from .stiff import replace_ions

# Define the Chernoff face plotting function
def plot(df, 
         name,
         cations = ['Na + K', 'Ca', 'Mg'],
         anions = ['Cl', 'HCO3', 'SO4'],
         unit='mg/L', 
         figname='Stiff diagram', 
         figformat='jpg',
         sep = True,
         ax = None):    
    
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

    
    # Plot the Chernoff faces for each sample
    # -------------------------------------------------------------------------
    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111, aspect='equal')
    
    # Normalizar valores para que estén en un rango razonable [0, 1]
    # para que las caras no se deformen demasiado
    cmax = max(cat_max, an_max) if max(cat_max, an_max) > 0 else 1
    
    Labels = []
    for i in range(len(df)):
        try:
            # Usar valores normalizados
            v_cat1 = cat1[i] / cmax
            v_cat2 = cat2[i] / cmax
            v_cat3 = cat3[i] / cmax
            v_an1 = an1[i] / cmax
            v_an2 = an2[i] / cmax
            v_an3 = an3[i] / cmax

            x1 = 0.90       # height  of upper face
            x2 = 0.40       # overlap of lower face
            x3 = 0.53       # half of vertical size of face
            
            x4 = v_cat3  # width of upper face, Mg
            x5 = v_cat2  # width of lower face, Ca
            x6 = v_cat1  # length of nose, Na+K
            
            x7 = 0.50       # vertical position of mouth
            x8 = v_an3   # curvature of mouth, SO4
            x9 = v_an2   # width of mouth, HCO3
            
            x10 = 0.73      # vertical position of eyes
            x11 = 0.47      # separation of eyes
            
            x12 = 0.89      # slant of eyes 
            x13 = 0.47      # eccentricity of eyes
            x14 = v_an1  # size of eyes Cl
            x15 = 0.96      # position of pupils
            x16 = 0.98      # vertical position of eyebrows
            x17 = 0.22      # slant of eyebrows
            x18 = 0.27      # size of eyebrows
            
            # transform some values so that input between 0,1 yields variety of output
            x3 = 1.9 * (x3 - 0.5)
            x4 = x4 + 0.25
            x5 = x5 + 0.25
            x6 = 0.3 * (x6 + 0.01)
            x8 = 5 * (x8 + 0.001)
            x11 /= 5
            x12 = 2 * (x12 - 0.5)
            x13 += 0.05
            x14 += 0.1
            x15 = 0.5 * (x15 - 0.5)
            x16 = 0.25 * x16
            x17 = 0.5*(x17 - 0.5)
            x18 = 0.5*(x18 + 0.1)

            # Top of face
            e = matplotlib.patches.Ellipse( (0,(x1+x3)/2), 2*x4, (x1-x3), 
                                           fc='white', edgecolor='black', linewidth=2)
            ax.add_artist(e)
        
            # Bottom of face
            e = matplotlib.patches.Ellipse( (0,(-x1+x2+x3)/2), 2*x5, (x1+x2+x3), 
                                           fc='white', edgecolor='black', linewidth=2)
            ax.add_artist(e)
        
            # Cover overlaps
            e = matplotlib.patches.Ellipse( (0,(x1+x3)/2), 2*x4, (x1-x3), 
                                           fc='white', edgecolor='black', ec='none')
            ax.add_artist(e)
            e = matplotlib.patches.Ellipse( (0,(-x1+x2+x3)/2), 2*x5, (x1+x2+x3), 
                                           fc='white', edgecolor='black', ec='none')
            ax.add_artist(e)
            
            # Draw nose
            ax.plot([0,0], [-x6/2, x6/2], 'k')
            
            # Draw mouth
            p = matplotlib.patches.Arc( (0,-x7+.5/x8), 1/x8, 1/x8, 
                                       theta1=270-180/pi*arctan(x8*x9), 
                                       theta2=270+180/pi*arctan(x8*x9))
            ax.add_artist(p)
            
            # Draw eyes
            p = matplotlib.patches.Ellipse( (-x11-x14/2,x10), x14, x13*x14, 
                                           angle=-180/pi*x12, 
                                           facecolor='white', edgecolor='black')
            ax.add_artist(p)
            
            p = matplotlib.patches.Ellipse( (x11+x14/2,x10), x14, x13*x14, 
                                           angle=180/pi*x12, 
                                           facecolor='white', edgecolor='black')
            ax.add_artist(p)
        
            # Draw pupils
            p = matplotlib.patches.Ellipse( (-x11-x14/2-x15*x14/2, x10), .05, .05, 
                                           facecolor='black')
            ax.add_artist(p)
            p = matplotlib.patches.Ellipse( (x11+x14/2-x15*x14/2, x10), .05, .05, 
                                           facecolor='black')
            ax.add_artist(p)
            
            # Draw eyebrows
            ax.plot([-x11-x14/2-x14*x18/2,-x11-x14/2+x14*x18/2],
                    [x10+x13*x14*(x16+x17),x10+x13*x14*(x16-x17)],'k')
            ax.plot([x11+x14/2+x14*x18/2,x11+x14/2-x14*x18/2],
                    [x10+x13*x14*(x16+x17),x10+x13*x14*(x16-x17)],'k')
            
            # Show the explanation only if it's a single plot and it's the first face
            if len(df) == 1:
                ax.text(1.3, 1.2, f'Explanation', ha='left', va='top', fontsize=10)
                ax.text(1.3, 0.9, f'Face Up: {cations_label[2]}', ha='left', va='top', fontsize=8)
                ax.text(1.3, 0.6, f'Face Down: {cations_label[1]}', ha='left', va='top', fontsize=8)
                ax.text(1.3, 0.3, f'Nose: {cations_label[0]}', ha='left', va='top', fontsize=8)
                ax.text(1.3, 0.0, f'Mouth Curv: {anions_label[2]}', ha='left', va='top', fontsize=8)
                ax.text(1.3, -0.3, f'Mouth Width: {anions_label[1]}', ha='left', va='top', fontsize=8)
                ax.text(1.3, -0.6, f'Eyes Size: {anions_label[0]}', ha='left', va='top', fontsize=8)
            
            ax.set_aspect('equal')
            ax.axis([-1.2, 1.2, -1.2, 1.2])
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(name, fontsize=12, weight='normal')
    
        except(ValueError):
            pass
    return ax
