from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Union, Dict, Any
import logging

logger = logging.getLogger(__name__)

class ErrorHandler:
    async def __call__(self, request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(f"Необработанная ошибка: {str(e)}", exc_info=True)
            
            # Определяем тип ошибки и соответствующий код статуса
            status_code = 500
            if hasattr(e, 'status_code'):
                status_code = e.status_code
            
            # Формируем ответ об ошибке
            error_response: Dict[str, Any] = {
                "detail": str(e),
                "error_code": type(e).__name__,
                "path": request.url.path
            }
            
            if status_code == 500:
                # Для внутренних ошибок сервера скрываем детали
                error_response["detail"] = "Внутренняя ошибка сервера"
            
            return JSONResponse(
                status_code=status_code,
                content=error_response
            )
