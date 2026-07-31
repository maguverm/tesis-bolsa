from pydataxm.pydatasimem import ReadSIMEM
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path

# Parámetros de descarga
DATASET_ID = '96D56E'
FECHA_INICIO = '2013-01-01'
FECHA_FIN = datetime.today().strftime('%Y-%m-%d')
VARIABLE = 'PPBOGReal'
MESES_POR_BLOQUE = 6
MAX_WORKERS = 4

# Orden de versiones de más a menos definitiva
ORDEN_VERSIONES = ['TXF', 'TX6', 'TX5', 'TX4', 'TX3', 'TX2', 'TX1', 'TXR']

# Ruta de salida
RUTA_SALIDA = Path(__file__).resolve().parents[2] / 'data' / 'raw' / 'precio_bolsa.parquet'


def generar_bloques(fecha_inicio, fecha_fin, meses):
    """Genera lista de tuplas (inicio, fin) por bloques de N meses."""
    bloques = []
    inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    while inicio < fin:
        fin_bloque = min(inicio + relativedelta(months=meses), fin)
        bloques.append((inicio.strftime('%Y-%m-%d'), fin_bloque.strftime('%Y-%m-%d')))
        inicio = fin_bloque + relativedelta(days=1)
    return bloques


def descargar_bloque(args):
    """Descarga un bloque de fechas y retorna el DataFrame filtrado."""
    dataset_id, fecha_inicio, fecha_fin, variable = args
    try:
        dataset = ReadSIMEM(dataset_id, fecha_inicio, fecha_fin)
        df = dataset.main(filter=False)
        df = df[df['CodigoVariable'] == variable]
        return df
    except Exception as e:
        print(f"Error en bloque {fecha_inicio} - {fecha_fin}: {e}")
        return pd.DataFrame()


def mejor_version(df):
    """Para cada día, toma el valor de la versión más definitiva disponible."""
    version_cat = pd.CategoricalDtype(categories=ORDEN_VERSIONES, ordered=True)
    df['Version'] = df['Version'].astype(version_cat)
    idx = df.groupby('Fecha')['Version'].transform('min') == df['Version']
    return df[idx].drop_duplicates('Fecha').sort_values('Fecha').reset_index(drop=True)


def descargar_precio_bolsa():
    print(f"Descargando precio de bolsa desde {FECHA_INICIO} hasta {FECHA_FIN}...")

    bloques = generar_bloques(FECHA_INICIO, FECHA_FIN, MESES_POR_BLOQUE)
    print(f"Total de bloques: {len(bloques)}")

    args = [(DATASET_ID, inicio, fin, VARIABLE) for inicio, fin in bloques]

    resultados = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futuros = {executor.submit(descargar_bloque, arg): arg for arg in args}
        for i, futuro in enumerate(as_completed(futuros), 1):
            df_bloque = futuro.result()
            if not df_bloque.empty:
                resultados.append(df_bloque)
            print(f"Bloque {i}/{len(bloques)} completado")

    df = pd.concat(resultados, ignore_index=True)
    df = mejor_version(df)

    os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
    df.to_parquet(RUTA_SALIDA, index=False)

    print(f"\nDescarga completa: {len(df)} registros guardados en {RUTA_SALIDA}")
    print(df['Version'].value_counts())
    return df


if __name__ == '__main__':
    df = descargar_precio_bolsa()
    print(df.head())