import pandas as pd
import os
from pathlib import Path

URL_RONI = 'https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt'
RUTA_SALIDA = Path(__file__).resolve().parents[2] / 'data' / 'raw' / 'oni.parquet'

MES_CENTRAL = {
    'DJF': 1, 'JFM': 2, 'FMA': 3, 'MAM': 4,
    'AMJ': 5, 'MJJ': 6, 'JJA': 7, 'JAS': 8,
    'ASO': 9, 'SON': 10, 'OND': 11, 'NDJ': 12
}

def descargar_oni():
    print("Descargando índice RONI desde NOAA...")
    df = pd.read_csv(URL_RONI, sep=r'\s+', header=0)
    df.columns = ['SEAS', 'YR', 'ANOM']
    
    df['Mes'] = df['SEAS'].map(MES_CENTRAL)
    df['Fecha'] = pd.to_datetime(df[['YR', 'Mes']].rename(
        columns={'YR': 'year', 'Mes': 'month'}).assign(day=1))
    
    df = df[['Fecha', 'ANOM']].rename(columns={'ANOM': 'ONI'})
    df = df.sort_values('Fecha').reset_index(drop=True)
    
    # Agregar julio 2026 con forward fill
    julio_2026 = pd.DataFrame([{
        'Fecha': pd.Timestamp('2026-07-01'),
        'ONI': df['ONI'].iloc[-1]
    }])
    df = pd.concat([df, julio_2026], ignore_index=True)
    print(f"Julio 2026 agregado con ONI = {julio_2026['ONI'].values[0]}")
    
    os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
    df.to_parquet(RUTA_SALIDA, index=False)
    
    print(f"Descarga completa: {len(df)} registros guardados")
    print(f"Rango: {df['Fecha'].min()} — {df['Fecha'].max()}")
    print(df.tail())

if __name__ == '__main__':
    descargar_oni()