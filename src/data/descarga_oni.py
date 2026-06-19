import pandas as pd
import os

URL_ONI = 'https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt'
RUTA_SALIDA = r'C:\proyectos\tesis-bolsa\data\raw\oni.parquet'

# Mes central de cada trimestre móvil
MES_CENTRAL = {
    'DJF': 1, 'JFM': 2, 'FMA': 3, 'MAM': 4,
    'AMJ': 5, 'MJJ': 6, 'JJA': 7, 'JAS': 8,
    'ASO': 9, 'SON': 10, 'OND': 11, 'NDJ': 12
}

def descargar_oni():
    print("Descargando índice ONI desde NOAA...")
    df = pd.read_csv(URL_ONI, sep='\s+')
    
    df['Mes'] = df['SEAS'].map(MES_CENTRAL)
    df['Fecha'] = pd.to_datetime(df[['YR', 'Mes']].rename(columns={'YR': 'year', 'Mes': 'month'}).assign(day=1))
    
    df = df[['Fecha', 'ANOM']].rename(columns={'ANOM': 'ONI'})
    df = df.sort_values('Fecha').reset_index(drop=True)
    
    os.makedirs(os.path.dirname(RUTA_SALIDA), exist_ok=True)
    df.to_parquet(RUTA_SALIDA, index=False)
    
    print(f"Descarga completa: {len(df)} registros guardados")
    print(f"Rango: {df['Fecha'].min()} — {df['Fecha'].max()}")
    print(df.head())

if __name__ == '__main__':
    descargar_oni()