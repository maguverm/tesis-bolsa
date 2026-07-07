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
MESES_POR_BLOQUE = 1

ORDEN_VERSIONES = ['TXF', 'TX6', 'TX5', 'TX4', 'TX3', 'TX2', 'TX1', 'TXR']

DATASETS = {
    'demanda_real': {
        'id': '14fabb',
        'fecha_inicio': '2021-01-01',
        'col_fecha': 'FechaHora',
        'tiene_versiones': True,
        'archivo': BASE / 'demanda_real.parquet'
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
    idx = df.groupby([col_fecha, 'CodigoSICAgente'])['Version'].transform('min') == df['Version']
    return df[idx]


def descargar_dataset(nombre, config):
    fecha_fin = datetime.today().strftime('%Y-%m-%d')
    print(f"\nDescargando {nombre} desde {config['fecha_inicio']} hasta {fecha_fin}...")

    bloques = generar_bloques(config['fecha_inicio'], fecha_fin, MESES_POR_BLOQUE)
    print(f"Total de bloques: {len(bloques)}")

    archivo = config['archivo']
    os.makedirs(os.path.dirname(archivo), exist_ok=True)

    # Detectar bloques ya descargados
    if os.path.exists(archivo):
        df_existente = pd.read_parquet(archivo)
        ultima_fecha = pd.to_datetime(df_existente[config['col_fecha'] if config['col_fecha'] == 'Fecha' else 'Fecha']).max()
        bloques = [(ini, fin) for ini, fin in bloques if datetime.strptime(fin, '%Y-%m-%d') > ultima_fecha]
        print(f"Reanudando desde {ultima_fecha.date()} — bloques pendientes: {len(bloques)}")
    else:
        df_existente = pd.DataFrame()

    args = [(config['id'], inicio, fin) for inicio, fin in bloques]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futuros = {executor.submit(descargar_bloque, arg): arg for arg in args}
        for i, futuro in enumerate(as_completed(futuros), 1):
            df_bloque = futuro.result()
            if not df_bloque.empty:
                if config['tiene_versiones']:
                    df_bloque = mejor_version(df_bloque, config['col_fecha'])
                if config['col_fecha'] != 'Fecha':
                    df_bloque = df_bloque.rename(columns={config['col_fecha']: 'Fecha'})

                # Guardar incrementalmente
                if os.path.exists(archivo):
                    df_prev = pd.read_parquet(archivo)
                    df_bloque = pd.concat([df_prev, df_bloque], ignore_index=True)

                df_bloque.sort_values('Fecha').reset_index(drop=True).to_parquet(archivo, index=False)
                print(f"  Bloque {i}/{len(bloques)} guardado")
            else:
                print(f"  Bloque {i}/{len(bloques)} vacío o con error")

    df_final = pd.read_parquet(archivo)
    print(f"\nTotal registros: {len(df_final)}")
    print(f"Rango: {df_final['Fecha'].min()} — {df_final['Fecha'].max()}")


if __name__ == '__main__':
    for nombre, config in DATASETS.items():
        descargar_dataset(nombre, config)
    print("\nDescarga de demanda completa.")