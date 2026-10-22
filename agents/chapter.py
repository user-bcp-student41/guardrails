"""Rol chapter: edita aquí sus instrucciones y entregables."""

from graph.state import WorkflowState
from graph.context import _ctx, _runs, _const_block, _ronda, _feedback_block


INSTRUCTIONS = """Realiza la revisión final siguiendo esta secuencia:

1. Identifica y enumera todos los criterios de aceptación explícitos en el
   contexto y los contratos proporcionados. No inventes criterios. Si no se
   proporcionaron, indícalo y limita el veredicto a la evidencia disponible.
2. Contrasta cada criterio con todas las áreas:
   - Arquitectura: el arquitecto; verifica que el plan cubra el criterio y sea
     compatible con los contratos de las demás áreas.
   - Persistencia: responsable de Datos; verifica modelo, relaciones,
     restricciones y migraciones cuando exista entregable de Datos. Si no lo
     hay, revisa solo lo demostrable en los otros entregables e indica la
     limitación.
   - Implementación: responsables de Backend y Frontend/API; comprueba que los
     cambios implementen el criterio y respeten los contratos aprobados.
   - Pruebas: responsable de Pruebas; comprueba qué criterio cubre cada prueba
     y si el informe demuestra que fue ejecutada. No confundas pruebas
     propuestas con pruebas ejecutadas.
   - Seguridad: responsable de Seguridad; comprueba riesgos y hallazgos
     reportados, y si las medidas propuestas tienen evidencia de implementación.
3. Detecta contratos incompatibles entre áreas, criterios sin cobertura,
   hallazgos pendientes y pruebas que faltan. Sustenta cada observación con la
   evidencia disponible: archivo y líneas si se proporcionaron; de lo
   contrario, cita la sección o informe. No inventes ubicaciones ni resultados.
4. En rondas posteriores, revisa una por una las observaciones anteriores.
   Clasifica cada una como RESUELTA, PARCIALMENTE RESUELTA o PENDIENTE y explica
   la evidencia. Indica cuáles deben volver a desarrollo.
5. Por cada observación pendiente, especifica:
   - Responsable por rol (Arquitectura, Datos, Backend, Frontend/API, Pruebas o
     Seguridad).
   - Cambio concreto requerido.
   - Verificación reproducible necesaria y su estado: EJECUTADA, PENDIENTE o
     NO VERIFICADO, solo cuando la evidencia permita determinarlo.
6. Emite el informe con este formato:
   - Resumen del resultado.
   - Tabla de criterios: criterio | arquitectura | persistencia | implementación
     | pruebas | seguridad | evidencia/resultado.
   - Observaciones pendientes: hallazgo | evidencia | responsable | cambio
     requerido | verificación.
   - Observaciones anteriores: hallazgo | estado | evidencia | acción de
     seguimiento. Si es la primera ronda, indícalo.
   - Pruebas pendientes y limitaciones de evidencia.
   - Una única línea final: VEREDICTO: APROBADO, APROBADO CON OBSERVACIONES o
     RECHAZADO.

Usa APROBADO solo si no quedan brechas, hallazgos ni verificaciones pendientes.
Usa APROBADO CON OBSERVACIONES si quedan correcciones o verificaciones no
bloqueantes; usa RECHAZADO si existe un incumplimiento bloqueante. Justifica la
decisión con evidencia. No afirmes que se ejecutaron pruebas ni que una
corrección está comprobada si el contexto no lo demuestra; marca lo no
verificado como NO VERIFICADO.

Conserva las aprobaciones humanas: este informe y su veredicto técnico no las
sustituyen, conceden ni revocan.
"""


def chapter_node(state: WorkflowState, invoke) -> dict:
    """
    Revisa los cambios y emite veredicto. Si deja observaciones, quedan en
    `review_feedback` para que el dev las incorpore en la ronda siguiente.

    Usa `context` como checklist de compliance.
    Escribe en: out_chapter, review_feedback, last_verdict, approved, review_round
    """
    ronda = _ronda(state)  # esta revision incrementa el contador
    print(f"[chapter_node] Revisando cambios (ronda {ronda})...")

    reports = "\n\n".join(
        f"## {label}\n{_ctx(state.get(field, ''), 6000)}"
        for field, label in (
            ("out_analysis", "Análisis de arquitectura"),
            ("out_backend", "Implementación backend"),
            ("out_frontend", "Implementación frontend/API"),
            ("out_testing", "Pruebas"),
            ("out_security", "Seguridad"),
        )
    )

    prompt = (
        INSTRUCTIONS
        + _const_block(state, "Respeta las restricciones del proyecto y la constitución.")
        + "\nRepositorio: "
        + state["repo_name"]
        + "\nNodo: Eres el Chapter del equipo.\n"
        + f"\nRonda de revisión: {ronda}"
        + "\nCriterios de aceptación y contexto:\n"
        + _ctx(state.get("context", ""), 6000)
        + "\nCódigo y evidencia original:\n"
        + _ctx(state.get("snapshot", ""), 6000)
        + "\nPlan / arquitectura:\n"
        + _ctx(state.get("out_plan", ""), 2500)
        + "\nInformes y entregas:\n"
        + reports
    )
    if state.get("include_data"):
        prompt += (
            "\nContrato e implementación de Datos y persistencia:\n"
            + _ctx(state.get("out_data", ""), 6000)
        )
    else:
        prompt += "\nDatos y persistencia: no hay entregable separado en esta ejecución; "
        prompt += "contrasta lo que pueda verificarse en el plan, código y demás informes."
    if ronda > 1:
        prompt += (
            "\nObservaciones de rondas anteriores — verifica cada una y detalla "
            "cuáles deben volver a desarrollo:\n"
            + _ctx(state.get("review_feedback", ""), 6000)
        )
    prompt += "\nEmite el veredicto final con el formato requerido."
    salida = invoke(prompt)
    veredicto = parse_verdict(salida)

    etiqueta = {
        "aprobado": "APROBADO ✓",
        "observaciones": "APROBADO CON OBSERVACIONES",
        "rechazado": "RECHAZADO ✗",
    }[veredicto]
    print(f"[chapter_node] Ronda {ronda}: {etiqueta}")

    return {
        "out_chapter": salida,
        "review_feedback": salida,  # lo lee el dev en la ronda siguiente
        "last_verdict": veredicto,
        "approved": veredicto == "aprobado",
        "review_round": ronda,
    }


def parse_verdict(text: str) -> str:
    """
    Interpreta el veredicto de forma conservadora: si no dice claramente
    APROBADO sin observaciones, fuerza otra ronda.

    Retorna: "aprobado" | "observaciones" | "rechazado"
    """
    t = (text or "").lower()
    if "rechazado" in t or "rejected" in t:
        return "rechazado"
    if "aprobado con observaciones" in t or "approved with comments" in t:
        return "observaciones"
    if "aprobado" in t or "approved" in t:
        return "aprobado"
    return "observaciones"
