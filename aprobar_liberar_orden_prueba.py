from __future__ import annotations

from pathlib import Path
from motor_ordenes_produccion import (
    MotorOrdenesProduccion,
    ErrorProduccion,
)

DB = Path(r"C:\Users\jrive\visual\erp_cafe.db")
ORDEN_ID = 1
USUARIO = "jrive"


def mostrar_orden(motor):
    orden = motor.obtener_orden(ORDEN_ID)
    print("\nORDEN")
    print("-" * 84)
    print(f"ID:                 {orden['id']}")
    print(f"Número:             {orden['numero']}")
    print(f"Producto:           {orden['producto_nombre']} {orden['producto_presentacion']}")
    print(f"Fórmula:            {orden['formula_codigo']} v{orden['formula_version']}")
    print(f"Cantidad programada:{orden['cantidad_programada']} {orden['unidad']}")
    print(f"Lote:               {orden['lote_planeado']}")
    print(f"Estado actual:       {orden['estado']}")
    return orden


def mostrar_disponibilidad(motor):
    print("\nDISPONIBILIDAD DE MATERIALES")
    print("-" * 84)
    resultados = motor.validar_disponibilidad(ORDEN_ID)
    todos_ok = True
    for item in resultados:
        estado = "OK" if item.cumple else "FALTANTE"
        todos_ok = todos_ok and item.cumple
        print(
            f"{estado:8} {item.componente:24} {item.presentacion:10} "
            f"Req.: {item.requerido:10.4f} | "
            f"Disp.: {item.disponible:10.4f} | "
            f"Falta: {item.faltante:10.4f} {item.unidad}"
        )
    return todos_ok


def main():
    print("=" * 84)
    print("SIGA ERP — APROBACIÓN Y LIBERACIÓN DE ORDEN DE PRODUCCIÓN")
    print("=" * 84)
    print(f"Base de datos: {DB}")
    print(f"Orden objetivo: ID {ORDEN_ID}")

    try:
        motor = MotorOrdenesProduccion(DB, usuario=USUARIO)
        orden = mostrar_orden(motor)

        estado = str(orden["estado"]).strip().upper()

        if estado in {"LIBERADA", "EN PROCESO", "TERMINADA", "CERRADA"}:
            print("\nLa orden ya superó la fase de aprobación y liberación.")
            input("\nPresione ENTER para cerrar...")
            return

        if estado == "ANULADA":
            print("\nERROR: La orden está ANULADA y no puede continuar.")
            input("\nPresione ENTER para cerrar...")
            return

        if not mostrar_disponibilidad(motor):
            print("\nRESULTADO: NO APTO PARA LIBERAR.")
            print("No se realizarán cambios.")
            input("\nPresione ENTER para cerrar...")
            return

        print("\nACCIONES")
        print("1. Aprobar la orden si todavía está PLANEADA.")
        print("2. Liberar la orden.")
        print("3. Registrar ambos cambios en el historial.")
        print("4. No descontar inventario.")
        print("5. No registrar consumos.")
        print("6. No iniciar la ejecución física.")

        confirmacion = input(
            "\nPara aprobar y liberar escriba exactamente LIBERAR: "
        ).strip().upper()

        if confirmacion != "LIBERAR":
            print("\nOperación cancelada. No se realizaron cambios.")
            input("\nPresione ENTER para cerrar...")
            return

        orden = motor.obtener_orden(ORDEN_ID)
        estado = str(orden["estado"]).strip().upper()

        if estado == "PLANEADA":
            motor.aprobar(
                ORDEN_ID,
                "Orden aprobada durante la prueba operativa controlada."
            )
            print("\nOrden aprobada correctamente.")
        elif estado == "BORRADOR":
            motor.cambiar_estado(
                ORDEN_ID,
                "PLANEADA",
                "Orden planeada durante la prueba operativa controlada."
            )
            motor.aprobar(
                ORDEN_ID,
                "Orden aprobada durante la prueba operativa controlada."
            )
            print("\nOrden planeada y aprobada correctamente.")
        elif estado == "APROBADA":
            print("\nLa orden ya estaba aprobada.")
        else:
            raise ErrorProduccion(
                f"No se puede continuar desde el estado {estado}."
            )

        motor.liberar(
            ORDEN_ID,
            "Orden liberada después de validar materiales disponibles."
        )

        final = motor.obtener_orden(ORDEN_ID)

        print("\n" + "=" * 84)
        print("OPERACIÓN COMPLETADA")
        print("=" * 84)
        print(f"Orden: {final['numero']}")
        print(f"Estado final: {final['estado']}")
        print(f"Aprobada por: {final['aprobada_por']}")
        print(f"Aprobada en:  {final['aprobada_en']}")
        print(f"Liberada por: {final['liberada_por']}")
        print(f"Liberada en:  {final['liberada_en']}")
        print("\nInventario sin cambios.")
        print("La orden queda lista para iniciar ejecución.")

    except Exception as exc:
        print("\nERROR")
        print("-" * 84)
        print(f"{type(exc).__name__}: {exc}")
        print("Revise el mensaje antes de continuar.")

    input("\nPresione ENTER para cerrar...")


if __name__ == "__main__":
    main()
