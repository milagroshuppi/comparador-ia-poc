"""
Comparador de IA - Prueba de concepto (PoC)

Corre un mismo conjunto de tareas contra varias "configuraciones" de IA
(distintos modelos o distintos prompts de sistema), mide cada respuesta con
criterios definidos y genera un reporte comparativo en Markdown y CSV.

Uso:
    python comparador.py --demo                 # sin API key, con respuestas de ejemplo
    python comparador.py                        # usa la API de Claude (requiere ANTHROPIC_API_KEY)
    python comparador.py --tareas tareas/mis_tareas.json
"""

import argparse
import csv
import json
import os
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

# Configuraciones a comparar: cada una es un modelo + un prompt de sistema.
CONFIGURACIONES = [
    {
        "nombre": "rapido-directo",
        "modelo": "claude-haiku-5-5",
        "sistema": "Respondé en español, de forma breve y directa.",
    },
    {
        "nombre": "potente-estructurado",
        "modelo": "claude-sonnet-5-5",
        "sistema": "Respondé en español. Organizá la respuesta en pasos o viñetas.",
    },
]


@dataclass
class Resultado:
    tarea: str
    configuracion: str
    modelo: str
    segundos: float
    palabras: int
    cubre_palabras_clave: float  # 0 a 1: proporción de palabras clave presentes
    respeta_limite: bool         # ¿quedó dentro del límite de palabras?
    puntaje: float               # puntaje final de 0 a 10
    respuesta: str


def cargar_tareas(ruta: Path) -> list[dict]:
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def pedir_respuesta(config: dict, prompt: str, demo: bool) -> str:
    """Obtiene la respuesta de la IA (o una simulada en modo demo)."""
    if demo:
        estilo = "- " if "estructurado" in config["nombre"] else ""
        return (
            f"{estilo}Respuesta de ejemplo de {config['nombre']} para: {prompt[:60]}. "
            "Una API permite que dos sistemas se comuniquen e intercambien datos. "
            "Por ejemplo, un banco expone una API para que un sistema de gestión registre pagos."
        )

    import anthropic  # se importa acá para que el modo demo no lo necesite

    cliente = anthropic.Anthropic()  # lee ANTHROPIC_API_KEY del entorno
    mensaje = cliente.messages.create(
        model=config["modelo"],
        max_tokens=600,
        system=config["sistema"],
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in mensaje.content if b.type == "text")


def evaluar(tarea: dict, respuesta: str) -> tuple[int, float, bool, float]:
    """Aplica los criterios definidos en la tarea y devuelve las métricas."""
    texto = respuesta.lower()
    palabras = len(respuesta.split())

    claves = [c.lower() for c in tarea.get("palabras_clave", [])]
    cobertura = sum(c in texto for c in claves) / len(claves) if claves else 1.0

    limite = tarea.get("max_palabras", 200)
    respeta = palabras <= limite

    # Puntaje: 7 puntos por cubrir los conceptos clave, 3 por respetar el largo pedido.
    puntaje = round(cobertura * 7 + (3 if respeta else 0), 1)
    return palabras, round(cobertura, 2), respeta, puntaje


def correr(tareas: list[dict], demo: bool) -> list[Resultado]:
    resultados = []
    for tarea in tareas:
        for config in CONFIGURACIONES:
            inicio = time.perf_counter()
            respuesta = pedir_respuesta(config, tarea["prompt"], demo)
            segundos = round(time.perf_counter() - inicio, 2)
            palabras, cobertura, respeta, puntaje = evaluar(tarea, respuesta)
            resultados.append(Resultado(
                tarea=tarea["id"], configuracion=config["nombre"], modelo=config["modelo"],
                segundos=segundos, palabras=palabras, cubre_palabras_clave=cobertura,
                respeta_limite=respeta, puntaje=puntaje, respuesta=respuesta,
            ))
            print(f"[{tarea['id']}] {config['nombre']}: {puntaje}/10 ({segundos}s)")
    return resultados


def guardar_reporte(resultados: list[Resultado], carpeta: Path, demo: bool) -> Path:
    carpeta.mkdir(exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d-%H%M%S")

    # CSV con todos los datos, para analizar en Excel o pandas
    with open(carpeta / f"resultados-{marca}.csv", "w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=list(asdict(resultados[0]).keys()))
        escritor.writeheader()
        escritor.writerows(asdict(r) for r in resultados)

    # Resumen por configuración
    resumen = {}
    for r in resultados:
        d = resumen.setdefault(r.configuracion, {"puntajes": [], "segundos": []})
        d["puntajes"].append(r.puntaje)
        d["segundos"].append(r.segundos)

    lineas = [
        "# Reporte comparativo",
        "",
        f"Fecha: {datetime.now():%d/%m/%Y %H:%M} · Modo: {'demo (respuestas simuladas)' if demo else 'API de Claude'}",
        "",
        "| Configuración | Puntaje promedio (0-10) | Tiempo promedio (s) |",
        "| --- | --- | --- |",
    ]
    ranking = sorted(resumen.items(), key=lambda kv: -sum(kv[1]["puntajes"]) / len(kv[1]["puntajes"]))
    for nombre, d in ranking:
        prom = sum(d["puntajes"]) / len(d["puntajes"])
        seg = sum(d["segundos"]) / len(d["segundos"])
        lineas.append(f"| {nombre} | {prom:.1f} | {seg:.2f} |")

    ganador = ranking[0][0]
    lineas += ["", f"**Recomendación:** `{ganador}` obtuvo el mejor puntaje promedio.", "", "## Detalle por tarea", ""]
    for r in resultados:
        lineas += [
            f"### {r.tarea} — {r.configuracion} ({r.puntaje}/10)",
            f"Palabras: {r.palabras} · Conceptos clave cubiertos: {r.cubre_palabras_clave:.0%} · "
            f"Dentro del límite: {'sí' if r.respeta_limite else 'no'}",
            "",
            "> " + r.respuesta.replace("\n", "\n> "),
            "",
        ]

    ruta = carpeta / f"reporte-{marca}.md"
    ruta.write_text("\n".join(lineas), encoding="utf-8")
    return ruta


def main():
    parser = argparse.ArgumentParser(description="Compara configuraciones de IA sobre un set de tareas.")
    parser.add_argument("--tareas", default="tareas/tareas.json", help="Archivo JSON con las tareas")
    parser.add_argument("--demo", action="store_true", help="Usar respuestas simuladas (sin API key)")
    parser.add_argument("--salida", default="reportes", help="Carpeta donde guardar los reportes")
    args = parser.parse_args()

    if not args.demo and not os.getenv("ANTHROPIC_API_KEY"):
        raise SystemExit("Falta ANTHROPIC_API_KEY. Configurala o corré con --demo.")

    tareas = cargar_tareas(Path(args.tareas))
    resultados = correr(tareas, args.demo)
    ruta = guardar_reporte(resultados, Path(args.salida), args.demo)
    print(f"\nReporte generado: {ruta}")


if __name__ == "__main__":
    main()
