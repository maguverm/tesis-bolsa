import requests
import pandas as pd
import os

URL = 'https://www.datos.gov.co/resource/mcec-87by.json?$limit=10000&$where=vigenciadesde>="2013-01-01T00:00:00.000"'
from pathlib import Path
RUTA_SALIDA = Path(__file__).resolve().parents[2] / 'data' / 'raw' / 'trm.parquet'

def descargar_trm():
    print("Descargando TRM desde datos.gov.co...")
    
    r = requests.get(URL)
    df = pd.DataFrame(r.json())
    
    df['Fecha'] = pd.to_datetime(df['vigenciadesde']).dt.normalize()
    df['TRM'] = df['valor'].astype(float)
    df = df[['Fecha', 'TRM']].sort_values('Fecha').reset_index(drop=True)
    
    os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
    df.to_parquet(RUTA_SALIDA, index=False)
    
    print(f"Descarga completa: {len(df)} registros guardados")
    print(f"Rango: {df['Fecha'].min()} — {df['Fecha'].max()}")
    print(df.head())

if __name__ == '__main__':
    descargar_trm()