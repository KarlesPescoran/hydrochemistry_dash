import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import numpy as np
from adjustText import adjust_text 
import pandas as pd
from adjustText import adjust_text
import textwrap

def TDS(df: pd.DataFrame, ax=None):
    
    x = np.array(df["CE"].tolist()).reshape(-1, 1)
    y = df["TDS"].tolist()
    model = LinearRegression().fit(x, y)
    y_pred = model.predict(x)
    r2 = r2_score(y, y_pred)
    model_coef = float(model.coef_[0])
    model_intercept = float(model.intercept_)
    model_text = (
        f"y = {model_coef:.4f}x + {model_intercept:.4f}\n"
        f"R² = {r2:.2f}"
    )

    sns.set_theme(style="whitegrid", rc={
        "axes.edgecolor": "black",
        "axes.linewidth": 1.5,
        "axes.spines.right": True,
        "axes.spines.top": True
    })
    
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 10), dpi=100)
    else:
        fig = ax.get_figure()

    sns.scatterplot(
        data=df, 
        x="CE", 
        y="TDS", 
        ax=ax,
        color="black", # Color de los puntos
        edgecolor="black"  # Borde de los puntos para un look más definido
    )
    # 2. Añadimos la línea de regresión (ci=None quita la sombra)
    sns.regplot(
        data=df, 
        x="CE", 
        y="TDS", 
        scatter=False,       
        ax=ax, 
        color="red", 
        line_kws={'linewidth': 2},
        ci = False
    )
    texts = []
    for index, row in df.iterrows():
        # ax.text(x, y, string)
        texto = ax.text(row['CE'], row['TDS'], row['id'], 
                        fontsize=9, color='darkblue')
        texts.append(texto)

    # 4. REPELER LOS TEXTOS (Estilo geom_text_repel)
    # Le añade una línea gris fina si el texto se aleja mucho del punto
    adjust_text(texts, ax=ax, arrowprops=dict(arrowstyle="-", color='gray', lw=1.5))

    ax.text(
        0.05, 0.95,                      # X=0.05 (5% desde la izquierda), Y=0.95 (5% desde arriba)
        model_text,                      # El texto o la variable que quieres mostrar (ej. model_text)
        transform=ax.transAxes,          # CLAVE: Activa las coordenadas relativas del gráfico
        fontsize=11,                     # Tamaño de la fuente
        verticalalignment='top',         # El punto de anclaje Y es la parte superior del texto
        horizontalalignment='left'#,      # El punto de anclaje X es la izquierda del texto
    )   

    # 3. Etiquetas
    ax.set_xlabel("Conductividad (uS/cm)")
    ax.set_ylabel("Solidos Totales Disueltos (mg/L)")
    
    return fig

def error(table, ax=None, xx = "id"):
    df = table.copy()
    #print(df)
    sns.set_theme(style="whitegrid", rc={
        "axes.edgecolor": "black",
        "axes.linewidth": 1.5,
        "axes.spines.right": True,
        "axes.spines.top": True
    })
    
    if ax is None:
        fig, ax = plt.subplots(figsize=(10, 10), dpi=100)
    else:
        fig = ax.get_figure()

    # -----------------------------------------------------------------
    # DETECCIÓN AUTOMÁTICA DE TIPO DE DATO EN 'id'
    # -----------------------------------------------------------------
    # Intentamos convertir a numérico. Si hay textos irremediables, 'errors="coerce"' pondrá NaN
    numeric_ids = pd.to_numeric(df[xx], errors="coerce")
    
    # Si la mayoría de los datos no son NaN, significa que la intención original es que sea NUMÉRICO
    es_numerico = numeric_ids.notna().sum() > (len(df) / 2)

    if es_numerico:
        # CASO A: Es numérico (ej: 105, 108, 120...). Respetamos sus distancias reales en X.
        df["_x_plot"] = numeric_ids
        es_categorico_puro = False
    else:
        # CASO B: Es categórico/texto (ej: "SH-05:10/02/2013"). Graficamos de forma secuencial.
        df["_x_plot"] = range(len(df))
        es_categorico_puro = True

    # -----------------------------------------------------------------
    # RENDERS DE SEABORN (Usando la columna unificada _x_plot)
    # -----------------------------------------------------------------
    if "EBI" in df.columns:
        df["EBIn"] = -df["EBI"]
        sns.lineplot( 
            data=df, 
            x="_x_plot", 
            y="EBI", 
            ax=ax, 
            marker="o",          
            markersize=8,        
            color="red", 
            linewidth=2
        )
        sns.lineplot( 
            data=df, 
            x="_x_plot", 
            y="EBIn", 
            marker="o",          
            markersize=8,        
            ax=ax, 
            color="red", 
            linewidth=2
        )
        
    sns.scatterplot(
        data=df, 
        x="_x_plot", 
        y="error", 
        ax=ax,
        color="black", 
        edgecolor="black"  
    )

    # -----------------------------------------------------------------
    # FORMATEO DINÁMICO DEL EJE X
    # -----------------------------------------------------------------
    if es_categorico_puro:
        # Si era texto, forzamos los ticks y reemplazamos por el string
        ax.set_xticks(df["_x_plot"])
        ax.set_xticklabels(df[xx].astype(str), rotation=45, ha="right")
        ax.set_xlabel(xx)
    else:
        # Si era numérico, dejamos que Matplotlib maneje la escala numérica normal automáticamente
        ax.set_xlabel(xx)

    ax.set_ylabel("error [%]")
    plt.tight_layout() 
    
    return fig


def ECA_plot(df: pd.DataFrame, 
             data_rel: pd.DataFrame, 
             yaxis: "none",
             parametro: str,
             eca_types: list,
             tipo: str,
             ejex: str,
             ax=None):
    
    eca_types = eca_types if isinstance(eca_types, list) else [eca_types]

    # 1. Filtrar la fila del parámetro en el DF de ECA
    row_param = data_rel[data_rel['label'] == parametro]

    par = row_param["par"].item()
    # 2. Filtrar datos del dataframe principal
    df_plot = df.dropna(subset=[par])
    
    # 4. Iniciar el gráfico
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 6))
    else:
        fig = ax.get_figure()

    if yaxis == "log10":
        ax.semilogy()

    # 5. Elegir tipo de gráfico
    if tipo == 'bar':
        paleta_estaciones = dict(zip(df_plot['Label'], df_plot['Color']))
        sns.barplot(data=df_plot, x=ejex, y=par, hue = 'Label',
                    palette=paleta_estaciones, ax=ax)
        
        # Si Seaborn suprimió la leyenda por redundancia (ej. Label == ejex),                                
        # forzamos la inclusión de las etiquetas añadiendo puntos invisibles                              
        handles, labels = ax.get_legend_handles_labels()                                         
        if not any(label in paleta_estaciones for label in labels):
            for label, color in paleta_estaciones.items():                                               
                ax.plot([], [], color=color, label=label, marker='s',
                         linestyle='None', markersize=10)  

    else:
        # Usamos Matplotlib puro para permitir mezcla de marcadores y personalización extrema
            Labels_vistos = set() # Set para rastrear qué etiquetas ya están en la leyenda
            
            for idx, row in df_plot.iterrows():
                # 1. Control de la leyenda (evitar duplicados)
                label_actual = row.get('Label', '')
                if pd.isna(label_actual) or label_actual == '':
                    label_plot = None
                elif label_actual not in Labels_vistos:
                    label_plot = label_actual
                    Labels_vistos.add(label_actual)
                else:
                    label_plot = None
                    
                # 2. Extraer atributos de la fila (con valores por defecto por si falta alguna columna)
                m = row.get('Marker', 'o')
                s = row.get('Size', 30)
                c = row.get('Color', 'black')
                a = row.get('Alpha', 0.6)
                
                marcadores_linea = ['+', 'x', '1', '2', '3', '4', '_', '|']
                borde = None if m in marcadores_linea else 'black'
                
                # 3. Dibujar el punto
                ax.scatter(
                    row[ejex], row[par],
                    marker=m,
                    s=s,
                    c=c,
                    alpha=a,
                    label=label_plot,
                    edgecolors=borde
                )

    # 6. Adicionar líneas de ECA
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink']

    # 1. Trazar líneas individuales y agrupar textos
    limites_agrupados = {}
    if eca_types:
        for i, col_name in enumerate(eca_types):
            valor_limite = row_param[col_name].item()
            
            if pd.notna(valor_limite):
                color = colors[i % len(colors)]
                
                # Trazar línea individual y añadirla a la leyenda
                ax.axhline(y=valor_limite, color=color, linestyle='--', linewidth=1.5, alpha=0.8, 
                            label=f"{textwrap.fill(col_name, width=30)}")
                
                # Agrupar en el diccionario para el texto
                if valor_limite not in limites_agrupados:
                    limites_agrupados[valor_limite] = [valor_limite]

        # 2. Crear los objetos de texto unidos
        textos_a_separar = []
        x_targets = [] # Guardaremos los X de las líneas
        y_targets = [] # Guardaremos los Y de las líneas

        x_pos = len(df_plot[ejex].unique()) - 0.5 # Posición X a la derecha

        for valor in limites_agrupados.keys():
            # Guardar coordenadas para que adjust_text las esquive
            x_targets.append(x_pos)
            y_targets.append(valor)
            
            t = ax.text(x_pos, valor, f' {valor}', 
                        color='black', va='bottom', fontweight='bold', fontsize=9)
            textos_a_separar.append(t)

        # 3. Aplicar repel a los textos para que no choquen entre sí ni con su línea de origen
        if textos_a_separar:
            adjust_text(
                textos_a_separar, 
                ax=ax,
                x=x_targets, 
                y=y_targets, 
                only_move={'text': 'y'},
                autoalign='y',
                force_points=(1.5, 1.5), 
                arrowprops=dict(arrowstyle="-", color='gray', lw=0.5)
            )

    # 4. Configuración del gráfico y leyenda
    ax.set_title(f'{parametro}')

    unidad = row_param['Unidad'].item() if 'Unidad' in row_param.columns else "Concentración"
    ax.set_ylabel(unidad)

    ax.tick_params(axis='x', rotation=45)
    ax.grid(axis='y', alpha=0.3)

    # Configurar la leyenda
    ax.legend(
            title="", 
            loc='upper center', 
            bbox_to_anchor=(0.5, -0.2), 
            ncol=3, 
            frameon=True
        )

    return fig
