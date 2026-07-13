import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from pathlib import Path
from statsmodels.tsa.seasonal import seasonal_decompose

# ── Configuración ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Precio de Bolsa - Colombia", layout="wide")

BASE = Path(__file__).resolve().parent / 'data' / 'processed'

@st.cache_data
def cargar_datos():
    df = pd.read_parquet(BASE / 'dataset_consolidado.parquet')
    if 'Fecha' in df.columns:
        df = df.set_index('Fecha')
    df.index = pd.to_datetime(df.index)
    df.index.name = 'Fecha'
    return df

df_full = cargar_datos()

VARIABLES = {
    'precio_bolsa': 'Precio de Bolsa ($/kWh)',
    'aportes_energia_gwh': 'Aportes Hídricos (GWh)',
    'vertimientos_energia_gwh': 'Vertimientos (GWh)',
    'gen_hidraulica': 'Generación Hidráulica',
    'gen_termica': 'Generación Térmica',
    'gen_solar': 'Generación Solar',
    'gen_eolica': 'Generación Eólica',
    'gen_cogenerador': 'Cogeneración',
    'disp_hidraulica': 'Disponibilidad Hidráulica',
    'disp_termica': 'Disponibilidad Térmica',
    'precio_escasez': 'Precio de Escasez ($/kWh)',
    'ONI': 'Índice ONI',
    'TRM': 'TRM ($/USD)'
}

def formato_eje_x(ax):
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.tick_params(axis='x', rotation=90)

# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.title("Filtros")
fecha_min = df_full.index.min().date()
fecha_max = df_full.index.max().date()

fecha_inicio = st.sidebar.date_input("Fecha inicio", value=fecha_min, min_value=fecha_min, max_value=fecha_max)
fecha_fin = st.sidebar.date_input("Fecha fin", value=fecha_max, min_value=fecha_min, max_value=fecha_max)

df = df_full.loc[str(fecha_inicio):str(fecha_fin)]

# ── Título ─────────────────────────────────────────────────────────────────────
st.title("Análisis Exploratorio — Precio de Bolsa de Energía en Colombia")
st.markdown(f"**Período seleccionado:** {fecha_inicio} → {fecha_fin} | **{len(df):,} días**")

# ── Sección 1: Precio de bolsa ─────────────────────────────────────────────────
st.header("1. Precio de Bolsa")

fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(df.index, df['precio_bolsa'], color='darkblue', linewidth=0.8)

eventos = {
    '2015-2016\nEl Niño': ('2015-07-01', 'red'),
    '2023-2024\nEl Niño': ('2023-07-01', 'red'),
    '2020-2022\nLa Niña': ('2020-09-01', 'steelblue'),
}
for label, (fecha, color) in eventos.items():
    f = pd.to_datetime(fecha)
    if df.index.min() <= f <= df.index.max():
        ax.axvline(f, color=color, linestyle='--', alpha=0.6, linewidth=1)
        ax.text(f, df['precio_bolsa'].max() * 0.95, label, fontsize=8, color=color, ha='center')

ax.set_ylabel('$/kWh')
ax.set_xlabel('')
formato_eje_x(ax)
sns.despine()
plt.tight_layout()
st.pyplot(fig)
plt.close()

# Estadísticas por año
st.subheader("Estadísticas descriptivas por año")
stats = df.groupby(df.index.year)['precio_bolsa'].agg(
    n='count', media='mean', std='std', min='min', max='max',
    p25=lambda x: x.quantile(0.25), p75=lambda x: x.quantile(0.75)
).round(2)
stats['cv'] = (stats['std'] / stats['media']).round(3)
stats.index.name = 'Año'
st.dataframe(stats, use_container_width=True)

# ── Sección 2: Explorador de variables ────────────────────────────────────────
st.header("2. Explorador de Variables en el Tiempo")

vars_seleccionadas = st.multiselect(
    "Selecciona variables:",
    options=list(VARIABLES.keys()),
    default=['precio_bolsa', 'gen_termica'],
    format_func=lambda x: VARIABLES[x]
)

estandarizar = st.checkbox("Estandarizar variables (Z-score)", value=True)

if vars_seleccionadas:
    fig, ax = plt.subplots(figsize=(14, 4))
    for var in vars_seleccionadas:
        serie = df[var]
        if estandarizar:
            serie = (serie - serie.mean()) / serie.std()
        ax.plot(df.index, serie, linewidth=0.8, label=VARIABLES[var])
    ax.set_ylabel('Z-score' if estandarizar else 'Valor')
    ax.set_xlabel('')
    formato_eje_x(ax)
    ax.legend(fontsize=8)
    sns.despine()
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

# ── Sección 3: Estadísticas descriptivas interactivas ─────────────────────────
st.header("3. Estadísticas Descriptivas por Año")

vars_stats = st.multiselect(
    "Selecciona variables para estadísticas:",
    options=list(VARIABLES.keys()),
    default=['precio_bolsa', 'ONI'],
    format_func=lambda x: VARIABLES[x],
    key='stats'
)

if vars_stats:
    for var in vars_stats:
        st.subheader(VARIABLES[var])
        stats_var = df.groupby(df.index.year)[var].agg(
            n='count', media='mean', std='std', min='min', max='max',
            p25=lambda x: x.quantile(0.25), p75=lambda x: x.quantile(0.75)
        ).round(2)
        stats_var.index.name = 'Año'
        st.dataframe(stats_var, use_container_width=True)

# ── Sección 4: Dispersión interactiva ─────────────────────────────────────────
st.header("4. Dispersión entre Variables")

col1, col2 = st.columns(2)
with col1:
    var_x = st.selectbox("Variable X:", options=list(VARIABLES.keys()),
                          format_func=lambda x: VARIABLES[x], index=4)
with col2:
    var_y = st.selectbox("Variable Y:", options=list(VARIABLES.keys()),
                          format_func=lambda x: VARIABLES[x], index=0)

fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(df[var_x], df[var_y], alpha=0.15, s=5, color='darkblue')
ax.set_xlabel(VARIABLES[var_x])
ax.set_ylabel(VARIABLES[var_y])
ax.tick_params(axis='x', rotation=90)
sns.despine()
plt.tight_layout()
st.pyplot(fig)
plt.close()

# ── Sección 5: Correlaciones ──────────────────────────────────────────────────
st.header("5. Matriz de Correlación (Spearman)")

vars_corr = st.multiselect(
    "Selecciona variables:",
    options=list(VARIABLES.keys()),
    default=list(VARIABLES.keys()),
    format_func=lambda x: VARIABLES[x],
    key='corr'
)

if len(vars_corr) >= 2:
    corr_matrix = df[vars_corr].corr(method='spearman')
    labels = [VARIABLES[v] for v in vars_corr]
    corr_matrix.index = labels
    corr_matrix.columns = labels

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm',
                center=0, ax=ax, annot_kws={'size': 8})
    ax.tick_params(axis='x', rotation=90)
    ax.tick_params(axis='y', rotation=0)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

# ── Sección 6: Descomposición ─────────────────────────────────────────────────
st.header("6. Descomposición de Serie de Tiempo")

var_decomp = st.selectbox(
    "Selecciona variable:",
    options=list(VARIABLES.keys()),
    format_func=lambda x: VARIABLES[x],
    key='decomp'
)

if len(df) >= 730:
    decomp = seasonal_decompose(df[var_decomp].dropna(), model='additive', period=365)
    fig, axes = plt.subplots(4, 1, figsize=(14, 10))
    for ax, serie, titulo in zip(axes,
        [decomp.observed, decomp.trend, decomp.seasonal, decomp.resid],
        ['Serie original', 'Tendencia', 'Estacionalidad', 'Residuos']):
        ax.plot(serie.index, serie, color='darkblue', linewidth=0.7)
        ax.set_title(titulo)
        ax.set_xlabel('')
        formato_eje_x(ax)
        sns.despine(ax=ax)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
else:
    st.warning("Se necesitan al menos 2 años de datos para la descomposición.")

# ── Sección 7: Precio vs ONI ──────────────────────────────────────────────────
st.header("7. Precio de Bolsa vs Índice ONI")

fig, ax1 = plt.subplots(figsize=(14, 4))
ax2 = ax1.twinx()
ax1.plot(df.index, df['precio_bolsa'], color='darkblue', linewidth=0.8, label='Precio de bolsa')
ax2.plot(df.index, df['ONI'], color='red', linewidth=1.2, label='ONI')
ax2.axhline(0.5, color='red', linestyle='--', alpha=0.4, linewidth=0.8)
ax2.axhline(-0.5, color='steelblue', linestyle='--', alpha=0.4, linewidth=0.8)
ax1.set_ylabel('$/kWh')
ax2.set_ylabel('Índice ONI', color='red')
ax2.tick_params(axis='y', colors='red')
formato_eje_x(ax1)
ax1.set_xlabel('')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left', fontsize=8)
ax1.set_title('Precio de Bolsa vs Índice ONI')
sns.despine()
plt.tight_layout()
st.pyplot(fig)
plt.close()