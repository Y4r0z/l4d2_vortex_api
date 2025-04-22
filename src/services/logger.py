import os
import logging
from logging.config import dictConfig
from pathlib import Path
import uuid
import time
import socket
from datetime import datetime

logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

SLOW_REQUEST_THRESHOLD = 0.3
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
HOSTNAME = socket.gethostname()

class RequestContextFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'request_id'):
            record.request_id = 'no_request'
        return True

class SecurityContextFilter(logging.Filter):
    def __init__(self, default_user_id='unknown'):
        super().__init__()
        self.default_user_id = default_user_id
        
    def filter(self, record):
        if not hasattr(record, 'user_id'):
            record.user_id = self.default_user_id
        return True

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)-10s - %(asctime)s - %(module)-15s : %(message)s"
        },
        "standard": {
            "format": "%(levelname)-10s - %(asctime)s - %(name)-15s : %(message)s"
        },
        "security": {
            "format": "%(levelname)-10s - %(asctime)s - %(module)-15s - [%(user_id)s] : %(message)s"
        }
    },
    "filters": {
        "request_context": {
            "()": RequestContextFilter
        },
        "security_context": {
            "()": SecurityContextFilter
        }
    },
    "handlers": {
        "console": {
            "level": LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "standard"
        },
        "console_error": {
            "level": "ERROR",
            "class": "logging.StreamHandler",
            "formatter": "standard"
        },
        "api_file": {
            "level": LOG_LEVEL,
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/api.log",
            "formatter": "verbose",
            "when": "midnight",
            "backupCount": 7,
            "filters": ["request_context"]
        },
        "db_file": {
            "level": LOG_LEVEL,
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/db.log",
            "formatter": "verbose",
            "when": "midnight",
            "backupCount": 7,
            "filters": ["request_context"]
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/error.log",
            "formatter": "verbose",
            "when": "midnight",
            "backupCount": 14,
            "filters": ["request_context"]
        },
        "integration_file": {
            "level": LOG_LEVEL,
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/integration.log",
            "formatter": "verbose",
            "when": "midnight",
            "backupCount": 7,
            "filters": ["request_context"]
        },
        "celery_file": {
            "level": LOG_LEVEL,
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/celery.log",
            "formatter": "verbose",
            "when": "midnight",
            "backupCount": 7
        },
        "security_file": {
            "level": LOG_LEVEL,
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/security.log",
            "formatter": "security",
            "when": "midnight",
            "backupCount": 30,
            "filters": ["security_context"]
        },
        "performance_file": {
            "level": LOG_LEVEL,
            "class": "logging.handlers.TimedRotatingFileHandler",
            "filename": "logs/performance.log",
            "formatter": "verbose",
            "when": "midnight",
            "backupCount": 14,
            "filters": ["request_context"]
        }
    },
    "loggers": {
        "api": {
            "handlers": ['console', 'api_file', 'error_file'],
            "level": LOG_LEVEL,
            "propagate": False
        },
        "db": {
            "handlers": ['console', 'db_file', 'error_file'],
            "level": LOG_LEVEL,
            "propagate": False
        },
        "integration": {
            "handlers": ['console', 'integration_file', 'error_file'],
            "level": LOG_LEVEL,
            "propagate": False
        },
        "integration.steam": {
            "handlers": ['console', 'integration_file', 'error_file'],
            "level": LOG_LEVEL,
            "propagate": False
        },
        "integration.rcon": {
            "handlers": ['console', 'integration_file', 'error_file'],
            "level": LOG_LEVEL,
            "propagate": False
        },
        "integration.sourcebans": {
            "handlers": ['console', 'integration_file', 'error_file'],
            "level": LOG_LEVEL,
            "propagate": False
        },
        "celery": {
            "handlers": ['console', 'celery_file', 'error_file'],
            "level": LOG_LEVEL,
            "propagate": False
        },
        "security": {
            "handlers": ['console', 'security_file', 'error_file'],
            "level": LOG_LEVEL,
            "propagate": False
        },
        "performance": {
            "handlers": ['console', 'performance_file'],
            "level": LOG_LEVEL,
            "propagate": False
        }
    }
}

def clear_log_files():
    log_files = [
        "logs/api.log",
        "logs/db.log", 
        "logs/error.log", 
        "logs/integration.log",
        "logs/celery.log", 
        "logs/security.log",
        "logs/performance.log"
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            with open(log_file, 'w') as f:
                f.truncate(0)

class ContextLogger:
    def __init__(self, logger):
        self.logger = logger
        
    def debug(self, msg, context=None, **kwargs):
        self._log(self.logger.debug, msg, context, **kwargs)
        
    def info(self, msg, context=None, **kwargs):
        self._log(self.logger.info, msg, context, **kwargs)
        
    def warning(self, msg, context=None, **kwargs):
        self._log(self.logger.warning, msg, context, **kwargs)
        
    def error(self, msg, context=None, exc_info=None, **kwargs):
        self._log(self.logger.error, msg, context, exc_info=exc_info, **kwargs)
        
    def exception(self, msg, context=None, **kwargs):
        self._log(self.logger.exception, msg, context, **kwargs)
        
    def _log(self, log_func, msg, context=None, **kwargs):
        if context:
            extra = kwargs.get('extra', {})
            extra['context'] = context
            kwargs['extra'] = extra
        log_func(msg, **kwargs)
    
    def addFilter(self, filter):
        self.logger.addFilter(filter)

def get_logger(name):
    return logging.getLogger(name)

# Создаем базовые логгеры
_api_logger = get_logger('api')
_db_logger = get_logger('db')
_integration_logger = get_logger('integration')
_steam_logger = get_logger('integration.steam')
_rcon_logger = get_logger('integration.rcon')
_sourcebans_logger = get_logger('integration.sourcebans')
_celery_logger = get_logger('celery')
_security_logger = get_logger('security')
_performance_logger = get_logger('performance')

# Применяем фильтры к базовым логгерам
_security_logger.addFilter(SecurityContextFilter())

# Создаем обертки с поддержкой контекста
api_logger = ContextLogger(_api_logger)
db_logger = ContextLogger(_db_logger)
integration_logger = ContextLogger(_integration_logger)
steam_logger = ContextLogger(_steam_logger)
rcon_logger = ContextLogger(_rcon_logger)
sourcebans_logger = ContextLogger(_sourcebans_logger)
celery_logger = ContextLogger(_celery_logger)
security_logger = ContextLogger(_security_logger)
performance_logger = ContextLogger(_performance_logger)

def init_logging():
    clear_log_files()
    dictConfig(LOGGING_CONFIG)
    
    api_logger.info("="*50)
    api_logger.info(f"Запуск приложения (версия: {APP_VERSION}, хост: {HOSTNAME})")
    api_logger.info("="*50)
    
    return {
        "api": api_logger,
        "db": db_logger,
        "integration": integration_logger,
        "steam": steam_logger,
        "rcon": rcon_logger,
        "sourcebans": sourcebans_logger,
        "celery": celery_logger,
        "security": security_logger,
        "performance": performance_logger
    }

async def log_slow_sql(query, params, duration, logger=None):
    if not logger:
        logger = db_logger
        
    context = {
        "duration": duration,
        "query": query,
        "params": params
    }
    
    if duration > 1.0:
        logger.warning(f"Очень медленный SQL запрос: {duration:.4f}s", context=context)
    elif duration > 0.5:
        logger.warning(f"Медленный SQL запрос: {duration:.4f}s", context=context)
    elif duration > 0.1:
        logger.info(f"SQL запрос с повышенной длительностью: {duration:.4f}s", context=context)

def setup_fastapi_logging(app):
    from fastapi import Request, FastAPI
    import time
    import contextvars
    
    request_id_var = contextvars.ContextVar('request_id', default=None)
    
    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request_id_var.set(request_id)
        start_time = time.time()

        path = request.url.path
        query = str(request.query_params) if request.query_params else ""
        client_host = request.client.host if request.client else "unknown"
        method = request.method
        
        log_context = {
            "request_id": request_id,
            "client_ip": client_host,
            "method": method,
            "path": path,
            "query": query,
            "user_agent": request.headers.get("user-agent", "unknown")
        }
        
        api_logger.info(f"Запрос: {method} {path}", context=log_context)

        try:
            response = await call_next(request)

            process_time = time.time() - start_time
            status_code = response.status_code
            
            log_context.update({
                "status_code": status_code,
                "duration": process_time
            })
            
            log_msg = f"Ответ: {method} {path} | Статус: {status_code} | Время: {process_time:.4f}s"
            
            if 200 <= status_code < 400:
                api_logger.info(log_msg, context=log_context)
            elif 400 <= status_code < 500:
                api_logger.warning(log_msg, context=log_context)
            else:
                api_logger.error(log_msg, context=log_context)
            
            if process_time > SLOW_REQUEST_THRESHOLD:
                perf_context = {
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration": process_time
                }
                performance_logger.warning(
                    f"Длительный запрос: {method} {path} | Время: {process_time:.4f}s",
                    context=perf_context
                )
                
            return response
        except Exception as e:
            process_time = time.time() - start_time
            error_context = {
                "request_id": request_id,
                "method": method,
                "path": path,
                "duration": process_time,
                "error": str(e)
            }
            api_logger.error(
                f"Ошибка при обработке {method} {path} после {process_time:.4f}s: {str(e)}", 
                context=error_context, 
                exc_info=True
            )
            raise

    def get_request_id():
        return request_id_var.get()
    
    app.state.get_request_id = get_request_id

    def log_auth_event(steam_id, event_type, success, details=None, ip=None, request_id=None):
        extra = {
            'user_id': steam_id,
            'request_id': request_id or get_request_id()
        }
        
        status = "успешно" if success else "неудачно"
        ip_info = f" с IP {ip}" if ip else ""
        
        context = {
            "event_type": event_type,
            "success": success,
            "ip": ip
        }
        
        if details:
            context["details"] = details
            
        msg = f"{event_type} {status}{ip_info}"
        if details:
            msg += f" - {details}"
            
        if success:
            security_logger.info(msg, extra=extra, context=context)
        else:
            security_logger.warning(msg, extra=extra, context=context)
    
    def log_privilege_change(admin_steam_id, target_steam_id, privilege_type, action, details=None, request_id=None):
        extra = {
            'user_id': admin_steam_id,
            'request_id': request_id or get_request_id()
        }
        
        context = {
            "admin_id": admin_steam_id,
            "target_id": target_steam_id,
            "privilege_type": privilege_type,
            "action": action
        }
        
        if details:
            context["details"] = details
            
        msg = f"Изменение привилегий: {action} {privilege_type} для {target_steam_id}"
        if details:
            msg += f" - {details}"
            
        security_logger.info(msg, extra=extra, context=context)
    
    app.state.log_auth_event = log_auth_event
    app.state.log_privilege_change = log_privilege_change
            
    @app.on_event("startup")
    async def startup_event():
        api_logger.info(f"FastAPI приложение запущено (версия: {APP_VERSION}, хост: {HOSTNAME})")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        api_logger.info("FastAPI приложение остановлено")
        
def setup_celery_logging():
    from celery.signals import task_prerun, task_postrun, task_failure, worker_ready
    
    @task_prerun.connect
    def task_prerun_handler(task_id, task, args, kwargs, **_):
        context = {
            "task_id": task_id,
            "task_name": task.name,
            "args": args,
            "kwargs": kwargs
        }
        celery_logger.info(f"Старт задачи {task.name} [{task_id}]", context=context)
    
    @task_postrun.connect
    def task_postrun_handler(task_id, task, args, kwargs, retval, **_):
        context = {
            "task_id": task_id,
            "task_name": task.name,
            "result_type": type(retval).__name__
        }
        celery_logger.info(f"Завершение задачи {task.name} [{task_id}]", context=context)
    
    @task_failure.connect
    def task_failure_handler(task_id, exception, args, kwargs, **_):
        context = {
            "task_id": task_id,
            "exception_type": type(exception).__name__,
            "exception": str(exception),
            "args": args,
            "kwargs": kwargs
        }
        celery_logger.error(f"Ошибка в задаче [{task_id}]: {exception}", context=context, exc_info=True)
    
    @worker_ready.connect
    def worker_ready_handler(**_):
        context = {
            "hostname": HOSTNAME,
            "app_version": APP_VERSION
        }
        celery_logger.info("Celery-worker запущен и готов принимать задачи", context=context)