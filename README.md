# Comparador de IA — Prueba de concepto

Herramienta en Python para **evaluar y comparar configuraciones de IA generativa** (distintos modelos de Claude o distintos prompts) sobre un mismo conjunto de tareas, con **criterios medibles** y un **reporte de conclusiones**.

Responde a una pregunta típica de un equipo de producto: *¿qué modelo o qué forma de pedirle las cosas a la IA conviene para este caso de uso?*

## Qué hace

1. Lee un set de tareas desde tareas/tareas.json (prompt, conceptos clave esperados, límite de palabras).
2. Envía cada tarea a cada configuración definida en CONFIGURACIONES.
3. Evalúa cada respuesta:
   - **Cobertura de conceptos clave** (7 puntos)
   - **Respeto del largo pedido** (3 puntos)
   - **Tiempo de respuesta**
4. Genera:
   - reportes/reporte-*.md: ranking, recomendación y detalle por tarea
   - reportes/resultados-*.csv: datos crudos para analizar en Excel o pandas

## Cómo usarlo

```bash
pip install -r requirements.txt

# Sin API key (respuestas simuladas, para probar el flujo)
python comparador.py --demo

# Con la API de Claude
export ANTHROPIC_API_KEY="tu-clave"
python comparador.py
```

Para probar tus propios casos, creá otro JSON con el mismo formato y pasalo con --tareas.

## Tests

```bash
pytest
```

## Tecnologías

Python 3 · API de Claude (Anthropic SDK) · CSV · pytest

## Próximos pasos

- Agregar un criterio de evaluación con "IA como juez" (otro modelo que califica la respuesta).
- Comparar herramientas de otros proveedores con la misma interfaz.
- Graficar los resultados.
