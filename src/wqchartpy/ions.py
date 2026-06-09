# -*- coding: utf-8 -*-
"""
Created on Tue Sep 14 13:41:09 2021

@author: Jing
"""
# Weight values are taken from hanford.dat provided by PFLOTRAN 
#   https://pflotran.org/.

CATIONS = [
    'Ca', 'Mg', 'Na', 'K', 'NH4',
    'Fe2', 'Fe3', 'Mn', 'Al', 'Sr', 'Ba',
    'Li', 'Rb', 'Cs',
    'Cu', 'Zn', 'Pb', 'Cd', 'Ni', 'Co',
    'Cr3', 'Cr6', 'Hg',
    'H'
]

ANIONS = [
    'Cl', 'SO4', 'CO3', 'HCO3',
    'NO3', 'NO2', 'PO4',
    'F', 'Br', 'I',
    'HS', 'S', 'OH'
]

ions_WEIGHT = {
    # Cationes mayores
    'Ca'   : 40.0780,
    'Mg'   : 24.3050,
    'Na'   : 22.9898,
    'K'    : 39.0983,
    'NH4'  : 18.0385,

    # Metales comunes
    'Fe2'  : 55.8450,
    'Fe3'  : 55.8450,
    'Mn'   : 54.9380,
    'Al'   : 26.9815,
    'Sr'   : 87.6200,
    'Ba'   : 137.3270,
    'Li'   : 6.9410,
    'Rb'   : 85.4678,
    'Cs'   : 132.9055,

    # Metales traza frecuentes
    'Cu'   : 63.5460,
    'Zn'   : 65.3800,
    'Pb'   : 207.2000,
    'Cd'   : 112.4140,
    'Ni'   : 58.6934,
    'Co'   : 58.9332,
    'Cr3'  : 51.9961,
    'Cr6'  : 51.9961,
    'Hg'   : 200.5900,

    # Aniones mayores
    'Cl'   : 35.4527,
    'SO4'  : 96.0636,
    'CO3'  : 60.0092,
    'HCO3' : 61.0171,
    'NO3'  : 62.0049,
    'NO2'  : 46.0055,
    'PO4'  : 94.9714,
    'F'    : 18.9984,
    'Br'   : 79.9040,
    'I'    : 126.9045,
    'HS'   : 33.0720,
    'S'    : 32.0650,
    'OH'   : 17.0073,

    # Catión ácido
    'H'    : 1.0079
}

ions_CHARGE = {
    'Ca'   : +2,
    'Mg'   : +2,
    'Na'   : +1,
    'K'    : +1,
    'NH4'  : +1,

    'Fe2'  : +2,
    'Fe3'  : +3,
    'Mn'   : +2,
    'Al'   : +3,
    'Sr'   : +2,
    'Ba'   : +2,
    'Li'   : +1,
    'Rb'   : +1,
    'Cs'   : +1,

    'Cu'   : +2,
    'Zn'   : +2,
    'Pb'   : +2,
    'Cd'   : +2,
    'Ni'   : +2,
    'Co'   : +2,
    'Cr3'  : +3,
    'Cr6'  : +6,
    'Hg'   : +2,

    'Cl'   : -1,
    'SO4'  : -2,
    'CO3'  : -2,
    'HCO3' : -1,
    'NO3'  : -1,
    'NO2'  : -1,
    'PO4'  : -3,
    'F'    : -1,
    'Br'   : -1,
    'I'    : -1,
    'HS'   : -1,
    'S'    : -2,
    'OH'   : -1,

    'H'    : +1
}

ions_label = {
    'Ca'   : "Ca$^{2+}$",
    'Mg'   : "Mg$^{2+}$",
    'Na'   : "Na$^+$",
    'K'    : "K$^+$",
    'NH4'  : "NH$_4^+$",

    'Fe2'  : "Fe$^{2+}$",
    'Fe3'  : "Fe$^{3+}$",
    'Mn'   : "Mn$^{2+}$",
    'Al'   : "Al$^{3+}$",
    'Sr'   : "Sr$^{2+}$",
    'Ba'   : "Ba$^{2+}$",
    'Li'   : "Li$^+$",
    'Rb'   : "Rb$^+$",
    'Cs'   : "Cs$^+$",

    'Cu'   : "Cu$^{2+}$",
    'Zn'   : "Zn$^{2+}$",
    'Pb'   : "Pb$^{2+}$",
    'Cd'   : "Cd$^{2+}$",
    'Ni'   : "Ni$^{2+}$",
    'Co'   : "Co$^{2+}$",
    'Cr3'  : "Cr$^{3+}$",
    'Cr6'  : "Cr$^{6+}$",
    'Hg'   : "Hg$^{2+}$",

    'Cl'   : "Cl$^-$",
    'SO4'  : "SO$_4^{2-}$",
    'CO3'  : "CO$_3^{2-}$",
    'HCO3' : "HCO$_3^-$",
    'NO3'  : "NO$_3^-$",
    'NO2'  : "NO$_2^-$",
    'PO4'  : "PO$_4^{3-}$",
    'F'    : "F$^-$",
    'Br'   : "Br$^-$",
    'I'    : "I$^-$",
    'HS'   : "HS$^-$",
    'S'    : "S$^{2-}$",
    'OH'   : "OH$^-$",
    'H'    : "H$^+$"
}