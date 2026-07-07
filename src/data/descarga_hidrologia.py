from pydataxm.pydatasimem import ReadSIMEM
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from pathlib import Path

BASE = Path(__file__).resolve().parents[2] / 'data' / 'raw'

# Parámetros generales
MAX_WORKERS = 4
MESES_POR_BLOQUE = 6

ORDEN_VERSIONES = ['TXF', 'TX6', 'TX5', 'TX4', 'TX3', 'TX2', 'TX1', 'TXR']

# Datasets a descargar
DATASETS = {
    'aportes_energia': {
        'id': 'BA1C55',
        'fecha_inicio': '2013-01-01',
        'col_fecha': 'Fecha',
        'tiene_versiones': False,
        'archivo': BASE / 'aportes_energia.parquet'
    },
    'vertimientos': {
        'id': 'AECA28',
        'fecha_inicio': '2013-01-01',
        'col_fecha': 'Fecha',
        'tiene_versiones': False,
        'archivo': BASE / 'vertimientos.parquet'
    },
    'nivel_embalse': {
        'id': 'BD26DC',
        'fecha_inicio': '2021-01-01',
        'col_fecha': 'FechaInicio',
        'tiene_versiones': True,
        'archivo': BASE / 'nivel_embalse.parquet'
    }
}


def generar_bloques(fecha_inicio, fecha_fin, meses):
    bloques = []
    inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
    fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
    while inicio < fin:
        fin_bloque = min(inicio + relativedelta(months=meses), fin)
        bloques.append((inicio.strftime('%Y-%m-%d'), fin_bloque.strftime('%Y-%m-%d')))
        inicio = fin_bloque + relativedelta(days=1)
    return bloques


def descargar_bloque(args):
    dataset_id, fecha_inicio, fecha_fin = args
    try:
        dataset = ReadSIMEM(dataset_id, fecha_inicio, fecha_fin)
        df = dataset.main(filter=False)
        return df
    except Exception as e:
        print(f"  Error en bloque {fecha_inicio} - {fecha_fin}: {e}")
        return pd.DataFrame()


def mejor_version(df, col_fecha):
    version_cat = pd.CategoricalDtype(categories=ORDEN_VERSIONES, ordered=True)
    df['Version'] = df['Version'].astype(version_cat)
    idx = df.groupby(col_fecha)['Version'].transform('min') == df['Version']
    return df[idx]


def descargar_dataset(nombre, config):
    fecha_fin = datetime.today().strftime('%Y-%m-%d')
    print(f"\nDescargando {nombre} desde {config['fecha_inicio']} hasta {fecha_fin}...")

    bloques = generar_bloques(config['fecha_inicio'], fecha_fin, MESES_POR_BLOQUE)
    print(f"Total de bloques: {len(bloques)}")

    args = [(config['id'], inicio, fin) for inicio, fin in bloques]

    resultados = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futuros = {executor.submit(descargar_bloque, arg): arg for arg in args}
        for i, futuro in enumerate(as_completed(futuros), 1):
            df_bloque = futuro.result()
            if not df_bloque.empty:
                resultados.append(df_bloque)
            print(f"  Bloque {i}/{len(bloques)} completado")

    df = pd.concat(resultados, ignore_index=True)

    if config['tiene_versiones']:
        df = mejor_version(df, config['col_fecha'])

    # Estandarizar nombre de columna fecha
    if config['col_fecha'] != 'Fecha':
        df = df.rename(columns={config['col_fecha']: 'Fecha'})

    df = df.sort_values('Fecha').reset_index(drop=True)

    os.makedirs(os.path.dirname(config['archivo']), exist_ok=True)
    df.to_parquet(config['archivo'], index=False)

    print(f"  {len(df)} registros guardados en {config['archivo']}")
    return df


if __name__ == '__main__':
    for nombre, config in DATASETS.items():
        descargar_dataset(nombre, config)
    print("\nDescarga de hidrología completa.")