"""
Prepara el dataset de fine-tuning para Mistral 7B (LoRA, mlx-lm), replicando
el mismo formato de prompt del baseline en 07_LLM.ipynb: ventana de 60 días
de precio_bolsa como contexto, predicción de un bloque de 7 valores
siguientes, sin variables exógenas.

Uso:
    python preparar_dataset_llm.py \
        --parquet data/processed/dataset_consolidado.parquet \
        --out-dir data/llm \
        --ventana 60 \
        --pasos 7 \
        --dias-valid 60

Salida: data/llm/{train,valid}.jsonl en formato "completions" de mlx-lm.
"""

import argparse
import json
from pathlib import Path

import pandas as pd


def serie_a_texto(serie, decimales=1):
    return ", ".join([str(round(v, decimales)) for v in serie])


def construir_prompt(contexto, pasos, ventana):
    texto_serie = serie_a_texto(contexto)
    return f"""Eres un experto en series de tiempo de precios de energía eléctrica en Colombia.
A continuación tienes los últimos {ventana} días del precio de bolsa en COP/kWh:

{texto_serie}

Continúa la serie prediciendo los siguientes {pasos} valores.
Responde ÚNICAMENTE con los {pasos} números separados por comas, sin texto adicional.
Los valores deben ser coherentes con la tendencia y el rango de la serie."""


def construir_ejemplos(precios, fechas, ventana, pasos, stride=1):
    ejemplos = []
    n = len(precios)
    for i in range(0, n - ventana - pasos + 1, stride):
        contexto = precios[i:i + ventana]
        objetivo = precios[i + ventana:i + ventana + pasos]

        prompt = construir_prompt(contexto, pasos, ventana)
        completion = " " + ", ".join(str(round(v, 1)) for v in objetivo)

        ejemplos.append({
            "prompt": prompt,
            "completion": completion,
            "fecha_inicio_objetivo": fechas[i + ventana].strftime("%Y-%m-%d"),
        })
    return ejemplos


def guardar_jsonl(ejemplos, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for ej in ejemplos:
            f.write(json.dumps(ej, ensure_ascii=False) + "\n")
    print(f"  {path}: {len(ejemplos)} ejemplos")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parquet", default="data/processed/dataset_consolidado.parquet")
    ap.add_argument("--out-dir", default="data/llm")
    ap.add_argument("--ventana", type=int, default=60)
    ap.add_argument("--pasos", type=int, default=7)
    ap.add_argument("--train-end", default="2025-07-12")
    ap.add_argument("--dias-valid", type=int, default=60)
    ap.add_argument("--stride", type=int, default=1)
    args = ap.parse_args()

    df = pd.read_parquet(args.parquet)
    if "Fecha" in df.columns:
        df = df.set_index("Fecha")
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()

    train_end = pd.Timestamp(args.train_end)
    serie_train = df[df.index <= train_end]["precio_bolsa"]

    corte_valid = train_end - pd.Timedelta(days=args.dias_valid)
    precios_train = serie_train[serie_train.index <= corte_valid].values
    fechas_train = serie_train[serie_train.index <= corte_valid].index

    precios_valid = serie_train.values
    fechas_valid = serie_train.index

    ejemplos_train = construir_ejemplos(precios_train, fechas_train, args.ventana, args.pasos, stride=args.stride)

    ejemplos_valid_todos = construir_ejemplos(precios_valid, fechas_valid, args.ventana, args.pasos, stride=args.pasos)
    ejemplos_valid = [e for e in ejemplos_valid_todos if pd.Timestamp(e["fecha_inicio_objetivo"]) > corte_valid]

    out_dir = Path(args.out_dir)
    guardar_jsonl(ejemplos_train, out_dir / "train.jsonl")
    guardar_jsonl(ejemplos_valid, out_dir / "valid.jsonl")

    print("\nEjemplo de prompt (train[0]):\n")
    print(ejemplos_train[0]["prompt"])
    print("\nCompletion esperado:", ejemplos_train[0]["completion"])


if __name__ == "__main__":
    main()