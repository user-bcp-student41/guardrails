"""Rol backend: edita aquí sus instrucciones y entregables."""

from graph.state import WorkflowState
from graph.context import _ctx, _runs, _const_block, _ronda, _feedback_block


INSTRUCTIONS = """Eres un desarrollador backend senior.
Implementa los endpoints y servicios del plan, respetando el contrato de API.
Valida las entradas y devuelve errores coherentes.
Define acceso a datos y transacciones. En equipos de seis cubre también esquema y migraciones; con Datos, consume su contrato sin duplicar sus migraciones y conserva los datos existentes.
Incluye un caso válido, un error y comandos para comprobarlos.
Devuelve los cambios con ### ruta/archivo.ext seguido de su bloque de código. Incorpora las observaciones del Chapter en las siguientes rondas."""

def backend_node(state: WorkflowState, invoke) -> dict:
    """
    Implementa los cambios de backend del plan.
    En rondas > 1 incorpora las observaciones del chapter.
    Se salta si project_type no incluye backend.
    Escribe en: out_backend
    """
    if not _runs(state, "backend"):
        print("[backend_node] project_type no incluye backend — saltando.")
        return {}

    print(f"[backend_node] Refactorizando backend (ronda {_ronda(state)})...")

    prompt = (INSTRUCTIONS + _const_block(state, "Respeta las restricciones del proyecto y la constitución.") + "\nRepositorio: " + state["repo_name"] + "\nPlan:\n" + _ctx(state.get("out_plan", ""),2500) + "\nCódigo original:\n" + _ctx(state.get("snapshot", ""),4000) + _feedback_block(state) + '\nPara código usa ### ruta/archivo.ext seguida de un bloque markdown.')
    if state.get("include_data"):
        prompt += "\nContrato aprobado de Datos y persistencia:\n" + _ctx(state.get("out_data", ""), 6000)
        prompt += "\nImplementa el acceso a datos según este contrato; no regeneres sus migraciones SQL."
    return {"out_backend": invoke(prompt)}
