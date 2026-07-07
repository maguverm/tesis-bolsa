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

DATASETS = {
    'generacion_real': {
        'id': 'E17D25',
        'fecha_inicio': '2013-01-01',
        'col_fecha': 'Fecha',
        'tiene_versiones': False,
        'archivo': BASE / 'generacion_real.parquet'
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
        ultima_fecha = pd.to_datetime(df_existente['Fecha']).max()
        bloques = [(ini, fin) for ini, fin in bloques if datetime.strptime(fin, '%Y-%m-%d') > ultima_fecha]
        print(f"Reanudando desde {ultima_fecha.date()} — bloques pendientes: {len(bloques)}")

    args = [(config['id'], inicio, fin) for inicio, fin in bloques]

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futuros = {executor.submit(descargar_bloque, arg): arg for arg in args}
        for i, futuro in enumerate(as_completed(futuros), 1):
            df_bloque = futuro.result()
            if not df_bloque.empty:
                if config['col_fecha'] != 'Fecha':
                    df_bloque = df_bloque.rename(columns={config['col_fecha']: 'Fecha'})

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
    print("\nDescarga de generación completa.")