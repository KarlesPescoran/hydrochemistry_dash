import io
import json
import re
import tempfile
import zipfile
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.wqchartpy import *  # noqa: F401,F403
from src.others import *  # noqa: F401,F403

APP_VERSION = "1.0"
PASSWORD = "srk2026"
PROJECT_EXT = ".hydroproj"

st.set_page_config(page_title="Hidroquímica - Dashboard", layout="wide")

st.markdown(
    """
    <style>
      html, body, [class*="css"] { font-size: 11px; }
      .stTabs [data-baseweb="tab"] { height: 2.1rem; }
      .stDataFrame, .stDataEditor { font-size: 11px; }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_state():
    defaults = {
        "logged_in": False,
        "cargado": False,
        "data_source_type": "local",
        "database_choice": "Si",
        "LD_choice": "NA",
        "local_data_dir": "data",
        "data_raw": None,
        "gwq_ui": None,
        "meqL_ui": None,
        "balance_table_ui": None,
        "categoric_columns": [],
        "numeric_columns": [],
        "filtered_indices": None,
        "data_filters": {},
        "figures": [],
        "EXIST_CE": False,
        "EXIST_TDS": False,
        "EXIST_PH": False,
        "project_message": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def clear_widget_keys(prefixes):
    for key in list(st.session_state.keys()):
        if any(key.startswith(p) for p in prefixes):
            del st.session_state[key]


def normalize_path_obj(p):
    return p if isinstance(p, Path) else Path(p)


def safe_df_for_pickle(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy(deep=True)


def serialize_geojson(gdf: gpd.GeoDataFrame | None):
    if gdf is None:
        return None
    try:
        return json.loads(gdf.to_json())
    except Exception:
        return None


def deserialize_geojson(obj):
    if not obj:
        return None
    try:
        return gpd.GeoDataFrame.from_features(obj["features"], crs=obj.get("crs", None))
    except Exception:
        return None


def register_fig(fig, name: str):
    if fig is None:
        return
    obj = fig[0] if isinstance(fig, tuple) else fig
    st.session_state.figures.append({"fig": obj, "name": name})


def as_figure(obj):
    if obj is None:
        return None
    if isinstance(obj, tuple):
        obj = obj[0]
    if hasattr(obj, "figure"):
        return obj.figure
    return obj


def figure_bytes(fig, fmt="png", dpi=150, width_cm=15, height_cm=15):
    fig = as_figure(fig)
    if fig is None:
        return None
    fig = fig.copy() if hasattr(fig, "copy") else fig
    fig.set_size_inches(width_cm / 2.54, height_cm / 2.54)
    buff = io.BytesIO()
    fig.savefig(buff, format=fmt, dpi=dpi, bbox_inches="tight")
    buff.seek(0)
    return buff.getvalue()


def _extract_zip_to_src(zip_path):
    src = {"data_raw": None}
    nombre_a_clave = {
        "estaciones_data.xlsx": "data_raw"
    }
    with zipfile.ZipFile(zip_path, "r") as zf:
        nombres_zip = zf.namelist()
        for nombre_zip in nombres_zip:
            base = Path(nombre_zip).name
            clave = nombre_a_clave.get(base)
            if clave is None:
                continue
            if not base.endswith(".shp"):
                with zf.open(nombre_zip) as f:
                    src[clave] = io.BytesIO(f.read())
            else:
                stem = Path(nombre_zip).stem
                parent = Path(nombre_zip).parent
                shp_archivos = [n for n in nombres_zip if Path(n).stem == stem and Path(n).parent == parent]
                tmp_dir = Path(tempfile.mkdtemp())
                for shp_file in shp_archivos:
                    dest = tmp_dir / Path(shp_file).name
                    with zf.open(shp_file) as f:
                        dest.write_bytes(f.read())
                src[clave] = tmp_dir / base
    return src


def _load_project_from_sources(src, source_type="mgl"):
    file_obj = src["data_raw"]
    if file_obj is None:
        raise FileNotFoundError("No se encontró data_raw")
        
    # Redundancia de seguridad para asegurar que el buffer no se lea vacío
    file_obj.seek(0) 

    # =========================
    # 1. CASO MGL (NORMAL)
    # =========================
    if source_type == "mgl":
        data_raw = fun.read_data(file_obj)
        
        # VALIDACIÓN: Verificar que data_raw no sea None
        if data_raw is None:
            raise ValueError("El archivo no pudo ser leído o está vacío.")
            
        if "id" not in data_raw.columns:
            data_raw.insert(0, "id", range(len(data_raw)))
            data_raw["id"] = data_raw["id"].astype(str)
        
        data_raw = data_raw[data_raw["id"].notna()]
            
        data_columns = data_raw.columns.tolist()
        categoric_columns = [col for col in data_columns if not pd.api.types.is_numeric_dtype(data_raw[col])]
        numeric_columns = [col for col in data_columns if pd.api.types.is_numeric_dtype(data_raw[col])]

        meqL = stiff.get_meqL(data_raw)
        if meqL is None:
            raise ValueError("Error al calcular meq/L. La función devolvió vacío.")

    # =========================
    # 2. CASO MEQ (INVERSO)
    # =========================
    elif source_type == "meq":
        meqL = fun.read_data(file_obj)
        
        # VALIDACIÓN: Verificar que meqL no sea None
        if meqL is None:
            raise ValueError("El archivo de meq/L no pudo ser leído o está vacío.")
        
        if "id" not in meqL.columns:
            meqL.insert(0, "id", range(len(meqL)))
            meqL["id"] = meqL["id"].astype(str)
        
        meqL = meqL[meqL["id"].notna()]

        data_raw = stiff.get_data_raw_from_meqL(meqL)
        if data_raw is None:
            raise ValueError("Error al convertir de meq a mg/L. La función devolvió vacío.")
            
        data_columns = data_raw.columns.tolist()
        categoric_columns = [col for col in data_columns if not pd.api.types.is_numeric_dtype(data_raw[col])]
        numeric_columns = [col for col in data_columns if pd.api.types.is_numeric_dtype(data_raw[col])]
    else:
        raise ValueError("source_type debe ser 'mgl' o 'meq'")

    # =========================
    # 3. UI FINAL
    # =========================
    # Asegúrate que meqL no sea None aquí
    ion_cols = meqL.columns 
    if "CE" in numeric_columns:
        base = data_raw[categoric_columns + ["CE"]].copy()
    else:
        base = data_raw[categoric_columns].copy()

    meqL_ui = pd.concat([base, meqL], axis=1)

    return {
        "data_raw": data_raw,
        "meqL_ui": meqL_ui,
        "categoric_columns": categoric_columns,
        "numeric_columns": numeric_columns,
        "stiff_figures": [],
        "balance_figures": []
    }



def get_balance_input(required_inputs):
    required_inputs = [re.findall(r"[A-Za-z0-9_]+", i) for i in required_inputs]
    return [item for sublist in required_inputs for item in sublist]


def apply_filters(df: pd.DataFrame, data_filters: dict) -> pd.Index:
    mask_global = pd.Series(True, index=df.index)
    for col, val in data_filters.items():
        if col not in df.columns:
            continue
        if val is None:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            mask = df[col].isna() | ((df[col] >= val[0]) & (df[col] <= val[1]))
        else:
            mask = df[col].isna() | df[col].astype(str).isin(val) if len(val) > 0 else pd.Series(True, index=df.index)
        mask_global &= mask
    return df.index[mask_global]


def filtered_data(df: pd.DataFrame) -> pd.DataFrame:
    idx = st.session_state.filtered_indices
    if idx is None:
        return df
    return df.loc[idx]


def piper_group_change(df: pd.DataFrame, col, group=None):
    if group == "none":
        df[col] = ""
        return df
    if group == "default":
        return df
    df[col] = st.session_state.data_raw[group]
    return df


def piper_atribute_change(df: pd.DataFrame, col, values_data=None):
    if values_data == "none":
        df[col] = fun.piper_atribute_ref[col]
        return df
    if values_data == "default":
        return df
    groups = df["Label"].unique().tolist()
    n = len(groups)
    if col == "Color":
        values = fun.get_color(values_data, n)
    else:
        marker_choices_tmp = fun.MARKERS[:n]
        while n > len(marker_choices_tmp):
            marker_choices_tmp = marker_choices_tmp + fun.MARKERS
        values = marker_choices_tmp[:n]
    color_map = dict(zip(groups, values))
    df[col] = df["Label"].map(color_map)
    return df


def piper_plot(df: pd.DataFrame):
    if st.session_state.piper_plottype_options == "triangle":
        return triangle_piper.plot(df, unit="mg/L", figname="triangle Piper diagram", figformat="jpg")
    if st.session_state.piper_plottype_options == "rectangle":
        return rectangle_piper.plot(df, unit="mg/L", figname="rectangle Piper diagram", figformat="jpg")
    if st.session_state.piper_plottype_options == "contour":
        return contour_piper.plot(df, unit="mg/L", figname="contour Piper diagram", figformat="jpg")
    return color_piper.plot(df, unit="mg/L", figname="color Piper diagram", figformat="jpg")


def check_stiff_input():
    required_inputs = st.session_state.stiff_cat1 + st.session_state.stiff_cat2 + st.session_state.stiff_cat3 + st.session_state.stiff_an1 + st.session_state.stiff_an2 + st.session_state.stiff_an3
    required_inputs = [re.findall(r"[A-Za-z0-9_]+", i) for i in required_inputs]
    required_inputs = [item for sublist in required_inputs for item in sublist]
    return all(ion_ in ions.ions_label for ion_ in required_inputs)


def build_balance_table():
    try:
        cations = st.session_state.balance_cat
        anions = st.session_state.balance_an
        balance_ions = get_balance_input(cations) + get_balance_input(anions)
        if st.session_state.EXIST_CE:
            balance_table = st.session_state.meqL_ui[st.session_state.categoric_columns + ["CE"] + balance_ions].copy()
            suma_cations = balance_table.eval("+".join(cations)).values
            suma_anions = balance_table.eval("+".join(anions)).values
            balance_table["error"] = (suma_cations - suma_anions) / (suma_cations + suma_anions) * 100
            balance_table["EBI"] = 1.2675 * (balance_table["CE"] ** (-0.5461)) * 100
        else:
            balance_table = st.session_state.meqL_ui[st.session_state.categoric_columns + balance_ions].copy()
            suma_cations = balance_table.eval("+".join(cations)).values
            suma_anions = balance_table.eval("+".join(anions)).values
            balance_table["error"] = (suma_cations - suma_anions) / (suma_cations + suma_anions) * 100
        balance_table = balance_table.iloc[st.session_state.filtered_indices]
        st.session_state.balance_table_ui = balance_table
    except Exception:
        st.session_state.balance_table_ui = pd.DataFrame()


def get_balance_table_view():
    balance_table = st.session_state.balance_table_ui.copy()
    if balance_table is None or balance_table.empty:
        return balance_table
    cations = st.session_state.balance_cat
    anions = st.session_state.balance_an
    balance_ions = get_balance_input(cations) + get_balance_input(anions)
    # for col in balance_ions + ["error", "CE", "EBI"]:
    #     if col in balance_table.columns:
    #         balance_table[col] = round(balance_table[col], 2)
    return balance_table


# def add_plot_to_figures(fig, name):
#     if fig is None:
#         return
#     st.session_state.figures.append({"fig": fig, "name": name})


def clear_loaded_data():
    st.session_state.cargado = False
    st.session_state.gwq_ui = None
    st.session_state.meqL_ui = None
    st.session_state.balance_table_ui = pd.DataFrame()
    st.session_state.categoric_columns = []
    st.session_state.numeric_columns = []
    st.session_state.filtered_indices = None
    st.session_state.data_filters = {}
    st.session_state.balance_figures = []
    st.session_state.stiff_figures = []
    st.session_state.EXIST_CE = False
    st.session_state.EXIST_TDS = False
    st.session_state.EXIST_PH = False
    clear_widget_keys([
        "f_", "load_", "balance_",
        "stiff_", "piper_",
    ])  

init_state()

with st.sidebar.expander("Proyecto"):
    source_type = st.radio(
        "Unidades de las concentraciones",
        ["mgl", "meq"],
        format_func=lambda x: "mg/L" if x == "mgl" else "meq/L",
        key="data_source_type",
    )
    data_file = st.file_uploader("Seleccione el archivo", type=["csv","xlsx"], key="data_file")
    if st.button("Procesar y cargar datos", key="load_data_btn"):
        try:
            clear_loaded_data()
            if data_file is None:
                st.error("No se subió ningún archivo")
                st.stop()
            src = {"data_raw": data_file}
            loaded = _load_project_from_sources(src, source_type)
            for k, v in loaded.items():
                st.session_state[k] = v

            st.session_state.cargado = True
            st.session_state.data_filters = {}
            st.session_state.balance_table_ui = pd.DataFrame()
            st.session_state.project_message = "Datos cargados correctamente desde archivo."
        except Exception as e:
            st.session_state.project_message = f"Error cargando datos: {type(e).__name__}: {e}"
            st.session_state.cargado = False
        
    if st.session_state.project_message:
        st.sidebar.info(st.session_state.project_message)

    if st.session_state.logged_in and st.session_state.cargado is False and st.session_state.data_raw is None:
        st.info("Carga un proyecto para ver la tabla editable, filtros y gráficas.")

# if not st.session_state.logged_in:
#     st.title("Hidroquímica")
#     pw = st.text_input("Ingrese la contraseña:", type="password", key="login_password")
#     if st.button("Ingresar", key="login_btn"):
#         if pw == PASSWORD:
#             st.session_state.logged_in = True
#             st.rerun()
#         else:
#             st.error("Contraseña incorrecta. Intente nuevamente.")
#     st.stop()

intro_tab, view_tables_tab, balance_tab, balance_graph_tab, stiff_tab, piper_tab = st.tabs([
    "Intro", "Tables", "Balance", "Balance gráficos", "Stiff", "Piper"
])
def export_figures_zip(tab_actual):

    dpi = st.session_state.export_dpi
    w_in = st.session_state.export_width / 2.54
    h_in = st.session_state.export_height / 2.54

    zip_buffer = io.BytesIO()
    tiene_contenido = False

    with zipfile.ZipFile(zip_buffer, "w") as zf:
        # CASO 1: Descargar desde la pestaña Balance gráficos
        if tab_actual == "balance":
            if "balance_figures" in st.session_state and st.session_state.balance_figures:
                tiene_contenido = True
                for item in st.session_state.balance_figures:
                    obj = item["fig"]
                    filename = item["name"]
                    fig = obj.figure if hasattr(obj, "figure") else obj
                    
                    fig.set_size_inches(w_in, h_in)
                    img_buffer = io.BytesIO()
                    fig.savefig(img_buffer, format="png", dpi=dpi, bbox_inches="tight")
                    img_buffer.seek(0)
                    zf.writestr(filename, img_buffer.read())
                    
        # CASO 2: Descargar desde la pestaña Stiff (Todos los generados en el caché)
        elif tab_actual == "stiff":
            if "stiff_figures" in st.session_state and st.session_state.stiff_figures:
                tiene_contenido = True
                for item in st.session_state.stiff_figures:
                    obj = item["fig"]
                    # Sanitizar nombre de archivo
                    nombre_limpio = re.sub(r'[\\/*?:"<>|]', "_", item["name"])
                    filename = f"stiff_{nombre_limpio}.png"
                    fig = obj.figure if hasattr(obj, "figure") else obj
                    
                    fig.set_size_inches(w_in, h_in)
                    img_buffer = io.BytesIO()
                    fig.savefig(img_buffer, format="png", dpi=dpi, bbox_inches="tight")
                    img_buffer.seek(0)
                    zf.writestr(filename, img_buffer.read())

    if not tiene_contenido:
        return None

    zip_buffer.seek(0)

    return zip_buffer.getvalue()

if st.session_state.cargado:
    st.divider()
    with st.sidebar.expander("Exportar"):
        st.number_input("Ancho (cm)", min_value=1.0, value=float(st.session_state.get("export_width", 15.0)), key="export_width")
        st.number_input("Alto (cm)", min_value=1.0, value=float(st.session_state.get("export_height", 15.0)), key="export_height")
        st.number_input("DPI", min_value=72, max_value=1200, value=int(st.session_state.get("export_dpi", 300)), key="export_dpi")
        
        # Informativo dinámico para el usuario
        st.write(f"📂 **Pestaña activa:** {st.session_state.get('tab_activa', 'Intro')}")
        
        if st.button("📦 Preparar gráficos para descarga", width=300):
            tab_actual = st.session_state.get("tab_activa", "Intro")
            with st.spinner("Compilando archivo ZIP específico..."):
                bytes_resultado = export_figures_zip(tab_actual)
                if bytes_resultado is not None:
                    st.session_state.zip_bytes = bytes_resultado
                    st.success(f"¡Gráficos de {tab_actual} listos!")
                else:
                    st.warning(f"No hay gráficos guardados o disponibles en la pestaña '{tab_actual}'.")

        if st.session_state.get("zip_bytes") is not None:
            tab_actual = st.session_state.get("tab_activa", "Intro")
            st.download_button(
                "📥 Descargar gráficos (.zip)",
                data=st.session_state.zip_bytes,
                file_name=f"graficos_{tab_actual.lower().replace(' ', '_')}.zip",
                mime="application/zip",
                width=300
            )

# Sidebar filters (original make_filters logic, compact)
if st.session_state.cargado:
    st.divider()
    with st.sidebar.expander("Filtros"):
        if st.button("Reset", key="reset_filters_btn"):
            st.session_state.data_filters = {}
            clear_widget_keys(["f_"])
            st.rerun()
        df_ref = st.session_state.data_raw
        for col in st.session_state.categoric_columns + st.session_state.numeric_columns:
            if pd.api.types.is_numeric_dtype(df_ref[col]):
                min_val = float(df_ref[col].min())
                max_val = float(df_ref[col].max())
                if min_val == max_val:
                    min_val -= min_val / 2
                    max_val += max_val / 2
                default = st.session_state.data_filters.get(col, (min_val, max_val))
                st.session_state.data_filters[col] = st.slider(col, min_val, max_val, default, key=f"f_{col}")
            else:
                choices = sorted(df_ref[col].dropna().astype(str).unique().tolist())
                default = st.session_state.data_filters.get(col, [])
                st.session_state.data_filters[col] = st.multiselect(col, choices, default=default, key=f"f_{col}")
        st.session_state.filtered_indices = apply_filters(df_ref, st.session_state.data_filters)
        # st.session_state.data_ui = st.session_state.data_raw.copy()
        # st.session_state.gwq_ui = fun.get_gwq(st.session_state.data_ui, clean=True)
        meqL = stiff.get_meqL(st.session_state.data_raw)
        if st.session_state.EXIST_CE or ("CE" in st.session_state.numeric_columns):
            st.session_state.EXIST_CE = True if "CE" in st.session_state.numeric_columns else st.session_state.EXIST_CE
            st.session_state.meqL_ui = pd.concat([st.session_state.data_raw[st.session_state.categoric_columns + (["CE"] if "CE" in st.session_state.data_raw.columns else [])], meqL], axis=1)
        else:
            st.session_state.meqL_ui = pd.concat([st.session_state.data_raw[st.session_state.categoric_columns], meqL], axis=1)
        st.session_state.anions = [col for col in st.session_state.meqL_ui.columns if col in ions.ANIONS]
        st.session_state.cations = [col for col in st.session_state.meqL_ui.columns if col in ions.CATIONS]
        st.session_state.EXIST_TDS = "TDS" in st.session_state.numeric_columns
        st.session_state.EXIST_PH = "pH" in st.session_state.numeric_columns


with intro_tab:

    st.title("🧪 Hidroquímica - Dashboard")
    st.caption("Herramienta avanzada para el análisis hidroquímico y balances iónicos.")
    
    st.markdown("---")
    
    # Organizar Consideraciones y Descargas en 2 columnas para optimizar espacio
    col_info, col_download = st.columns([3, 2], gap="large")
    
    with col_info:
        st.subheader("📋 Consideraciones del Archivo")
        st.info(
            """
            * **Formatos aceptados:** Archivos en `.csv` o `.xlsx`.
            * **Contenido admitido:** Parámetros fisicoquímicos, microbiológicos y cualquier variable categórica complementaria.
            * **Unidades de carga:** Los iones pueden ingresarse en **mg/L** (método estándar) o directamente en **meq/L** (si el usuario realizó un análisis previo y estimó los miliequivalentes).
            * **Cationes soportados:** 'Ca', 'Mg', 'Na', 'K', 'NH4', 'Fe2', 'Fe3', 'Mn', 'Al', 'Sr', 'Ba', 'Li', 'Rb', 'Cs', 'Cu', 'Zn', 'Pb', 'Cd', 'Ni', 'Co', 'Cr3', 'Cr6', 'Hg', 'H'.
            * **Aniones soportados:** 'Cl', 'SO4', 'CO3', 'HCO3', 'NO3', 'NO2', 'PO4', 'F', 'Br', 'I', 'HS', 'S', 'OH'.
            """
        )
        
    with col_download:
        st.subheader("📥 Plantillas ejemplo")
        st.write("Obtén plantillas de ejemplo")
        
        # Ejemplo de link estático que ya tenías
        st.markdown("🔗 [Descargar archivos de ejemplo básicos](https://your-link-here.com)")



if not st.session_state.cargado or st.session_state.data_raw is None:
    st.stop()

filtered_raw = filtered_data(st.session_state.data_raw).copy()
filtered_meqL = st.session_state.meqL_ui.loc[st.session_state.filtered_indices].reset_index(drop=True)

with view_tables_tab:
    st.divider()
    st.subheader("Datos brutos")
    st.dataframe(
        st.session_state.data_raw,
        width='stretch'
    )
    st.divider()
    st.subheader("Miliequivalentes")
    st.dataframe(
        st.session_state.meqL_ui,
        width='stretch'
    )


with balance_tab:
    st.session_state["tab_activa"] = "balance"  
    st.subheader("Balance")
    cat_col, an_col, = st.columns(2)
    with cat_col:
        valores_ideales = ["Na", "K", "Ca", "Mg"]
        cationes_disponibles = [cation for cation in valores_ideales if cation in st.session_state.cations]
        st.multiselect(
            "Cationes",
            options=st.session_state.cations,
            default=cationes_disponibles,
            key="balance_cat",
        )
    with an_col:
        valores_ideales = ["Cl", "HCO3", "SO4"]
        aniones_disponibles = [anion for anion in valores_ideales if anion in st.session_state.anions]
        st.multiselect(
            "Aniones",
            options=st.session_state.anions,
            default=aniones_disponibles,
            key="balance_an",
        )

    build_balance_table()

    st.dataframe(
        get_balance_table_view(),
        width='stretch'
    )



with balance_graph_tab:
    st.session_state["tab_activa"] = "balance"  
    st.session_state.balance_figures = []
    st.subheader("Balance")
    bal_mode_col1, bal_mode_col2, bal_mode_col3 = st.columns(3)
    with bal_mode_col1:
        balance_showtype_options = st.selectbox(
            "Tipo",
            ["TDS", "error"],
            key="balance_showtype_options"
        )
    with bal_mode_col2:
        st.selectbox(
            "Agrupar", ["none"] + st.session_state.categoric_columns,
            key="balance_group_options"
        )
    with bal_mode_col3:
        st.selectbox(
            "Color", ["none"] + st.session_state.categoric_columns,
            key="balance_color_options"
        )


    if balance_showtype_options == "TDS":
        if st.session_state.EXIST_TDS and st.session_state.EXIST_CE:
            fig = qc.TDS(filtered_raw)
            st.pyplot(fig)
            st.session_state.balance_figures.append({"fig": fig, "name": "tds.png"})
        else:
            st.write("Faltan los parámetros TDS y CE")

    else:
        if (
            st.session_state.balance_table_ui is None
            or st.session_state.balance_table_ui.empty
        ):
            st.warning(
                "Hubo un problema al generar la tabla de balance."
            )
        else:
            if st.session_state.EXIST_CE:
                fig = qc.error(
                    st.session_state.balance_table_ui
                )
                st.pyplot(fig)
                st.session_state.balance_figures.append({"fig": fig, "name": "balance_error.png"})
            else:
                st.write("Faltan el parámetro de CE")

with stiff_tab:
    st.session_state["tab_activa"] = "stiff"  
    st.session_state.figures = []
    current_option_filter = st.session_state.filtered_indices

    meqL_data = (
        st.session_state.meqL_ui
        .loc[current_option_filter]
        .copy()
        .reset_index(drop=True)
    )
    
    # =====================================
    # Inicialización
    # =====================================

    if "stiff_page" not in st.session_state:
        st.session_state.stiff_page = 1

    n_plots = len(meqL_data)
    print(n_plots)

    # =====================================
    # Cabecera
    # =====================================

    title_col, nav_col = st.columns([8, 2])

    with title_col:
        st.subheader("Stiff")

    with nav_col:
        c1, c2, c3, c4 = st.columns([1.5, 1, 1, 1])

        with c1:
            page_size = st.selectbox(
                "_",
                [25, 50, 100],
                index=0,
                key="stiff_page_size",
                label_visibility="collapsed"
            )

        # Calcular páginas una vez conocido page_size
        n_pages = max(1, (n_plots + page_size - 1) // page_size)

        # Evitar páginas fuera de rango
        st.session_state.stiff_page = min(st.session_state.stiff_page, n_pages)

        with c2:
            if st.button("◀", key="stiff_prev", width='stretch'):
                st.session_state.stiff_page = max(1, st.session_state.stiff_page - 1)

        with c3:
            if st.button("▶", key="stiff_next", width='stretch'):
                st.session_state.stiff_page = min(n_pages, st.session_state.stiff_page + 1)

        with c4:
            st.markdown(
                f"""
                <div style="
                    text-align:center;
                    padding-top:6px;
                    font-size:14px;
                ">
                    {st.session_state.stiff_page}/{n_pages}
                </div>
                """,
                unsafe_allow_html=True
            )

    # =====================================
    # Índices de la página actual
    # =====================================

    page = st.session_state.stiff_page
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, n_plots)
    plots_to_show = end_idx - start_idx

    # =========================
    # Opciones generales
    # =========================
    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

    with col1:
        st.text_input(
            "Título",
            value="{id}",
            key="stiff_title_options"
        )

    with col2:
        st.number_input(
            "Xlim",
            min_value=0.0,
            value=None,
            key="stiff_xlim_options"
        )

    with col3:
        st.selectbox(
            "Fondo",
            ["none", "red", "blue",
             "green", "black", "white", "yellow",
             "orange", "purple", "pink", "brown",
             "gray", "cyan", "magenta",
            ],
            key="stiff_background_options"
        )
    with col4:
        st.selectbox(
            "Labels",
            ["on", "off"],
            key="stiff_labels_options"
        )

    with col5:
        st.selectbox(
            "Agrupar",
            ["none"] + st.session_state.categoric_columns,
            key="stiff_group_options"
        )

    with col6:
        colores_disponibles = [
            "none", "white", "red", "blue", "green", "black", 
            "yellow", "orange", "purple", "pink", "brown", 
            "gray", "cyan", "magenta"
        ] + list(fun.PALETTES.keys())
        # Un input de texto libre
        color_escrito = st.text_input(
            "Color",
            value="none",
            key="stiff_color_options"
        )

    with col7:
        st.selectbox(
            "Línea",
            ["-", "--", ":", "-."],
            key="stiff_line_options"
        )
    # Un expansor o sugeridor rápido justo abajo si lo que escribió no está en la lista común
    if color_escrito.lower() not in colores_disponibles:
        st.caption("💡 ¡Puedes usar colores estándar como: " + ", ".join(colores_disponibles[:6]) + "...!")
    # =========================
    # Iones
    # =========================

    col_cat, col_an = st.columns(2)

    with col_cat:
        st.markdown("**Cationes**")

        c1, c2, c3 = st.columns(3)

        cat_keys = ["stiff_cat1", "stiff_cat2", "stiff_cat3"]
        label_keys_cat = ["stiff_cat1_lab", "stiff_cat2_lab", "stiff_cat3_lab"]
        # DICCIONARIO_LABELS = {
        #     "Na": "Sodio (Na⁺)",
        #     "Ca": "Calcio (Ca²⁺)",
        #     "Mg": "Magnesio (Mg²⁺)"
        # }

        # def sync_cat_labels():
        #     for i, k in enumerate(cat_keys):
        #         val = st.session_state.get(k, [])
        #         if val:
        #             ion_seleccionado = val[0]
        #             label_defecto = DICCIONARIO_LABELS.get(ion_seleccionado, ion_seleccionado)
        #             st.session_state[label_keys_cat[i]] = label_defecto

        for i, col in enumerate([c1, c2, c3]):
            with col:
                ideal_defaults = {0: "Na", 1: "Ca", 2: "Mg"}
                ideal_val = ideal_defaults[i]
                
                # 2. Verificar si el valor ideal existe en la lista de aniones disponibles
                if ideal_val in st.session_state.cations:
                    default_val = [ideal_val]
                else:
                    if len(st.session_state.cations) > i:
                        default_val = [st.session_state.cations[i]]
                    elif len(st.session_state.cations) > 0:
                        default_val = [st.session_state.cations[0]]
                    else:
                        default_val = []

                #3. Renderizar el multiselect de forma segura
                st.multiselect(
                    "_",
                    st.session_state.cations,
                    default=default_val,
                    key=cat_keys[i],
                    # on_change=sync_cat_labels,
                    label_visibility="collapsed"
                )

                # key_del_label = label_keys_cat[i]
        
                # # Si el usuario ya interactuó, el valor vive en session_state gracias a sync_cat_labels
                # if key_del_label in st.session_state:
                #     valor_actual_input = st.session_state[key_del_label]
                # else:
                #     # Si es la primera carga de la app, calculamos el valor inicial basándonos en default_val
                #     if default_val:
                #         ion_inicial = default_val[0]
                #         valor_actual_input = DICCIONARIO_LABELS.get(ion_inicial, ion_inicial)
                #     else:
                #         valor_actual_input = ""

                # # 3. Renderizar el text_input pasándole explícitamente el parámetro 'value'
                # st.text_input(
                #     "",
                #     value=valor_actual_input,
                #     key=key_del_label,
                #     label_visibility="collapsed"
                # )

    with col_an:
        st.markdown("**Aniones**")

        a1, a2, a3 = st.columns(3)

        an_keys = ["stiff_an1", "stiff_an2", "stiff_an3"]
        label_keys_an = ["stiff_an1_lab", "stiff_an2_lab", "stiff_an3_lab"]

        def sync_an_labels():
            for i, k in enumerate(an_keys):
                val = st.session_state.get(k, [])
                if val:
                    st.session_state[label_keys_an[i]] = val[0]

        for i, col in enumerate([a1, a2, a3]):
            with col:

                ideal_defaults = {0: "Cl", 1: "HCO3", 2: "SO4"}
                ideal_val = ideal_defaults[i]
                
                # 2. Verificar si el valor ideal existe en la lista de aniones disponibles
                if ideal_val in st.session_state.anions:
                    default_val = [ideal_val]
                else:
                    if len(st.session_state.anions) > i:
                        default_val = [st.session_state.anions[i]]
                    elif len(st.session_state.anions) > 0:
                        default_val = [st.session_state.anions[0]]
                    else:
                        default_val = []

                # 3. Renderizar el multiselect de forma segura
                st.multiselect(
                    "_",
                    st.session_state.anions,
                    default=default_val,
                    key=an_keys[i],
                    # on_change=sync_an_labels,
                    label_visibility="collapsed"
                )

                # st.text_input(
                #     "",
                #     key=label_keys_an[i],
                #     label_visibility="collapsed"
                # )

    # =========================
    # Validación
    # =========================

    if not check_stiff_input():
        st.warning("Ingrese iones válidos")

    else:
        ref_label = "Id" if "Id" in st.session_state.data_raw.columns else st.session_state.categoric_columns[0]
        meqL_data["Label"] = (
            st.session_state.data_raw
            .loc[current_option_filter, ref_label]
            .values
        )

        meqL_data["Color"] = "blue"
        meqL_data["Marker"] = st.session_state.stiff_line_options

        meqL_data = piper_group_change(meqL_data, "Label", st.session_state.stiff_group_options)
        meqL_data = piper_atribute_change(meqL_data, "Color", st.session_state.stiff_color_options)

        if n_plots == 0:
            st.info("No hay datos para mostrar")

        else:

            current_stiff_config = (
                tuple(current_option_filter),
                st.session_state.stiff_cat1,
                st.session_state.stiff_cat2,
                st.session_state.stiff_cat3,
                st.session_state.stiff_an1,
                st.session_state.stiff_an2,
                st.session_state.stiff_an3,
                st.session_state.stiff_title_options,
                st.session_state.stiff_xlim_options,
                st.session_state.stiff_background_options,
                st.session_state.stiff_labels_options,
                st.session_state.stiff_group_options,
                st.session_state.stiff_color_options,
                st.session_state.stiff_line_options,
            )

            if (
                "stiff_figures_cache" not in st.session_state
                or "stiff_config_cache" not in st.session_state
                or st.session_state.stiff_config_cache != current_stiff_config
            ):

                st.session_state.stiff_config_cache = current_stiff_config

                showlabel = (
                    st.session_state.stiff_labels_options == "on"
                )
                
                st.session_state.stiff_figures = []
                stiff_figures = []

                with st.spinner("Generando diagramas Stiff..."):

                    for i in range(len(meqL_data)):

                        df_s = meqL_data.iloc[[i]].reset_index(drop=True)

                        name = fun.renderize_name(
                            df_s,
                            st.session_state.stiff_title_options
                        )[0]

                        ax = stiff.plot(
                            df_s,
                            name=name,
                            cations=[
                                " + ".join(st.session_state.stiff_cat1),
                                " + ".join(st.session_state.stiff_cat2),
                                " + ".join(st.session_state.stiff_cat3),
                            ],
                            anions=[
                                " + ".join(st.session_state.stiff_an1),
                                " + ".join(st.session_state.stiff_an2),
                                " + ".join(st.session_state.stiff_an3),
                            ],
                            xlim=st.session_state.stiff_xlim_options,
                            backcolor=st.session_state.stiff_background_options,
                            showlabel=showlabel
                        )

                        fig = ax.figure

                        stiff_figures.append({"figure": fig, "name": name, "index": i})
                        st.session_state.stiff_figures.append({"fig": fig, "name": f"{i}_stiff_{name}.png"})

                st.session_state.stiff_figures_cache = stiff_figures
                

            stiff_figures = st.session_state.stiff_figures_cache

            st.caption(
                f"Mostrando diagramas {start_idx + 1}-{end_idx} de {n_plots}"
            )

            current_figures = stiff_figures[start_idx:end_idx]

            cols = 3

            for row_start in range(0, len(current_figures), cols):

                row_figures = current_figures[row_start:row_start + cols]
                columns = st.columns(cols)

                for col_idx, fig_info in enumerate(row_figures):

                    with columns[col_idx]:

                        st.pyplot(
                            fig_info["figure"],
                            width='stretch'
                        )