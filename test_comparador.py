from comparador import evaluar


def test_respuesta_completa_y_corta_tiene_puntaje_maximo():
    tarea = {"palabras_clave": ["pago", "reporte"], "max_palabras": 20}
    palabras, cobertura, respeta, puntaje = evaluar(tarea, "Registra el pago y genera un reporte.")
    assert cobertura == 1.0
    assert respeta is True
    assert puntaje == 10.0


def test_respuesta_larga_pierde_puntos_de_largo():
    tarea = {"palabras_clave": ["pago"], "max_palabras": 3}
    _, _, respeta, puntaje = evaluar(tarea, "El pago se registra automáticamente en el sistema.")
    assert respeta is False
    assert puntaje == 7.0


def test_sin_palabras_clave_cubiertas():
    tarea = {"palabras_clave": ["banco", "mail"], "max_palabras": 50}
    _, cobertura, _, puntaje = evaluar(tarea, "Respuesta que no menciona nada relevante.")
    assert cobertura == 0
    assert puntaje == 3.0
