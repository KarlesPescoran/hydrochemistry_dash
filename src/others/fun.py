import pandas as pd
import geopandas as gpd
import pathlib as Path
import seaborn as sns
import unicodedata   
import re

# def read_data(path: Path):
#     strategies = [
#         lambda: pd.read_csv(path.with_suffix(".csv")),
#         lambda: pd.read_excel(path.with_suffix(".xlsx"))
#     ]
#     for attempt in strategies:
#         try:
#             tmp = attempt()
#             if "Id" in tmp.columns:
#                 tmp = tmp[tmp["Id"].notna()]
#             return tmp
#         except Exception:
#             pass
#     KeyError(f"No se pudo leer {path}")
#     return None
def read_data(file_obj):
    # 1. Asegurar que el puntero esté al inicio por seguridad
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)
        
    # 2. Obtener el nombre del archivo para saber su extensión
    # st.file_uploader provee el atributo .name automáticamente
    filename = file_obj.name.lower()
    
    try:
        # 3. Intentar leer según la extensión real detectada
        if filename.endswith(".csv"):
            df = pd.read_csv(file_obj)
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_obj)
        else:
            raise ValueError("Formato de archivo no soportado (use CSV o XLSX)")
            
        # 4. Limpieza de filas vacías en la columna 'Id'
        if "Id" in df.columns:
            df = df[df["Id"].notna()]
            
        return df
        
    except Exception as e:
        # En lugar de un 'pass' que oculte el error, lanzamos la excepción real
        raise RuntimeError(f"Error procesando el archivo '{file_obj.name}': {e}")

def get_shp(path: Path):
    sf = gpd.read_file(path)
    sf = sf.to_crs("EPSG:4326")
    return sf

def get_stations(stations_path):
    if stations_path.exists():
        stations = gpd.read_file(stations_path)
        stations = stations.to_crs("EPSG:4326")
    else:
        stations = read_data(stations_path)
        stations = gpd.GeoDataFrame(
            stations,
            geometry=gpd.points_from_xy(stations.lon, stations.lat), crs="EPSG:4326"
        )
    return stations

def clean_data(df, cleaner = [], replace = "", omit = ["temporada", "id", "fecha", "zona"]):
    df = df.copy()
    cleaner = cleaner if isinstance(cleaner, list) else [cleaner]
    df_columns = df.columns.tolist()
    df_columns = [col for col in df_columns 
                  if col not in omit]

    for col in df_columns:
        df[col] = df[col].astype(str)
        
        for item in cleaner:

            df[col] = df[col].str.replace(item, replace)
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df

def limpiar_todo(texto):
    # 1. Quitar paréntesis y comas
    paso_1_2 = [re.sub(r"\(.*?\)|,.*", "", col).lower().strip() for col in texto]
    
    # 3. Quitar tildes (Descomponer y filtrar caracteres 'Mn' - Mark, Nonspacing)
    resultado = []
    for col in paso_1_2:
        # Normalizamos para separar la letra del acento
        nfd_form = unicodedata.normalize('NFD', col)
        # Filtramos: solo guardamos lo que NO sea un acento
        sin_tilde = "".join(c for c in nfd_form if unicodedata.category(c) != 'Mn')
        resultado.append(sin_tilde)
        
    return resultado

####################################################################################################
### WQCHARTPY ######################################################################################
####################################################################################################

def get_gwq(df: pd.DataFrame, clean = True, ions_name = []):
    df = df.copy()
    gwq = pd.DataFrame(columns=["Sample",	"Label",	"Color",	"Marker",	"Size",	"Alpha",
                                "pH",
                                "Ca",	"Mg",	"Na",	"K",	"HCO3",	"CO3",	"Cl",	"SO4",
                                "TDS"])
    if clean:
        df = clean_data(df, cleaner="<")
    #print(df.columns[2:])
    gwq["Sample"] = df["id"]
    if not "Label" in df.columns:
        gwq["Label"] = df["id"].values
    else:
        gwq["Label"] = df["Label"].values
    if not "Color" in df.columns:
        gwq["Color"] = "black"
    else:
        gwq["Color"] = df["Color"].values
    if not "Marker" in df.columns:
        gwq["Marker"] = "o"
    else:
        gwq["Marker"] = df["Marker"].values
    if not "Size" in df.columns:
        gwq["Size"] = 30
    else:
        gwq["Size"] = df["Size"].values
    if not "Alpha" in df.columns:
        gwq["Alpha"] = 0.6
    else:
        gwq["Alpha"] = df["Alpha"].values

    if "pH" in df.columns:
        gwq["pH"] = df["pH"]
    if "Ca" in df.columns:
        gwq["Ca"] = df["Ca"]
    if "Mg" in df.columns:
        gwq["Mg"] = df["Mg"]
    if "Na" in df.columns:
        gwq["Na"] = df["Na"]
    if "K" in df.columns:
        gwq["K"] = df["K"]
    if "HCO3" in df.columns:
        gwq["HCO3"] = df["HCO3"]
    if "CO3" in df.columns:
        gwq["CO3"] = df["CO3"]
    if "Cl" in df.columns:
        gwq["Cl"] = df["Cl"]
    if "SO4" in df.columns:
        gwq["SO4"] = df["SO4"]
    if "TDS" in df.columns:
        gwq["TDS"] = df["TDS"]

    for col in df.columns:
        if col in ions_name:
            gwq[col] = df[col]

    return gwq

piper_atribute_ref = {
    "Color": "black",
    "Marker": "o",
    "Size": 30,
    "Alpha": 0.6,
}


####################################################################################################
### THEMES #########################################################################################
####################################################################################################
MARKERS = ["o", "v", "^", "+", "x", "X",
           "<", ">", "8", "s", "p", "P",
           "*", "h", "H", "D", "d"]

PALETTES = {
    "deep": sns.color_palette("deep", 10).as_hex(),
    "muted": sns.color_palette("muted", 10).as_hex(),
    "pastel": sns.color_palette("pastel", 10).as_hex(),
    "bright": sns.color_palette("bright", 10).as_hex(),
    "dark": sns.color_palette("dark", 10).as_hex(),
    "colorblind": sns.color_palette("colorblind", 10).as_hex(),

    "tab10": sns.color_palette("tab10", 10).as_hex(),
    "tab20": sns.color_palette("tab20", 20).as_hex(),

    "Set1": sns.color_palette("Set1", 9).as_hex(),
    "Set2": sns.color_palette("Set2", 8).as_hex(),

    "viridis": sns.color_palette("viridis", 12).as_hex(),
    "plasma": sns.color_palette("plasma", 12).as_hex(),
    "Blues": sns.color_palette("Blues", 12).as_hex(),
    "Greens": sns.color_palette("Greens", 12).as_hex(),

    "coolwarm": sns.color_palette("coolwarm", 12).as_hex(),
    "Spectral": sns.color_palette("Spectral", 12).as_hex(),
    "RdBu": sns.color_palette("RdBu", 12).as_hex(),

    "custom_piper": [
        "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
        "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
        "#393b79", "#637939", "#8c6d31", "#843c39", "#7b4173"
    ]
}


def get_color(palette: str, n: int, repeat: bool = True):
    if palette in PALETTES:

        colors = PALETTES[palette]
        
        if n <= len(colors):
            return colors[:n]
        
        if not repeat:
            raise ValueError(
                f"La paleta '{palette}' solo tiene {len(colors)} colores (pediste {n})"
            )
        
        # repetir colores si necesitas más
        values = (colors * (n // len(colors) + 1))[:n]
  
    else:
        values = [palette]*n

    return values

def renderize_name(df: pd.DataFrame, plantilla: str) -> pd.Series:
    """
    Toma un DataFrame y un string plantilla. Extrae las variables del string,
    las mapea con las columnas del DataFrame (incluyendo combinaciones con '_')
    y devuelve una Serie de Pandas con los strings formateados por cada fila.
    """
    # 1. Encontrar todos los marcadores entre llaves {mini_plantilla}
    marcadores = re.findall(r"\{([^}]+)\}", plantilla)

    def procesar_fila(fila):
        # Convertimos la fila actual en un diccionario {columna: valor}
        valores_fila = fila.to_dict()
        ctx = {}
        
        # 2. Para cada marcador encontrado, resolvemos su valor dinámicamente
        for marcador in marcadores:
            # Si el marcador compuesto (ej: id_var) está formado por columnas reales
            partes = marcador.split('_')
            if all(p in valores_fila for p in partes):
                # Unimos los valores correspondientes con guion bajo
                ctx[marcador] = "_".join(str(valores_fila[p]) for p in partes)
            elif marcador in valores_fila:
                # Si es un marcador simple directo (ej: id)
                ctx[marcador] = valores_fila[marcador]
            else:
                # Si el marcador no coincide con tus columnas, lo dejamos igual
                ctx[marcador] = f"{{{marcador}}}"
                
        # 3. Reemplazar los valores en la plantilla para esta fila
        return plantilla.format(**ctx)

    # Aplicamos la lógica a lo largo del DataFrame (eje de las filas)
    generar = df.astype(str).apply(procesar_fila, axis=1)

    return generar