# src/core/error_handler.py
import sys
import logging
from typing import Type, Any

logger = logging.getLogger(__name__)

class ErrorHandler:
    """
    Gestiona el manejo centralizado de errores y excepciones no capturadas.
    """

    @classmethod
    def setup_global_exception_handling(cls):
        """
        Configura un hook global para capturar excepciones no manejadas.
        """
        sys.excepthook = cls._handle_exception
        logger.info("Manejo global de excepciones configurado.")

    @classmethod
    def _handle_exception(cls, exc_type: Type[BaseException], exc_value: BaseException, exc_traceback: Any):
        """
        Manejador de excepciones global que registra las excepciones no capturadas.
        """
        if issubclass(exc_type, KeyboardInterrupt):
            # No loguear KeyboardInterrupt, solo pasarlo al manejador por defecto
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.critical(
            "Excepción no capturada:",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
        # Opcional: Puedes añadir lógica para notificaciones, volcado de estado, etc.

# Example usage (for testing purposes, not part of the class itself)
if __name__ == "__main__":
    # Configurar un logger básico para la prueba
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    test_logger = logging.getLogger("TestErrorHandler")

    print("Configurando manejo global de excepciones...")
    ErrorHandler.setup_global_exception_handling()
    print("Manejo global de excepciones configurado.")

    def divide_by_zero():
        test_logger.info("Intentando división por cero...")
        result = 1 / 0
        print(result)

    def custom_error_function():
        test_logger.info("Lanzando un error personalizado...")
        raise ValueError("Este es un error de valor personalizado.")

    try:
        divide_by_zero()
    except ZeroDivisionError:
        test_logger.info("ZeroDivisionError capturado localmente. No debería ser manejado por el global.")

    print("\nLanzando una excepción no capturada (ValueError)...")
    custom_error_function()

    print("\nEste mensaje no debería aparecer si la excepción anterior no fue capturada.")