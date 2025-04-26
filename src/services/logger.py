import logging
import time
from pathlib import Path

from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

_logger_initialized = False

def clear_log_files():
	log_files = ["api.log", "error.log", "slow.log"]
	for file_name in log_files:
		log_path = log_dir / file_name
		if log_path.exists():
			with open(log_path, 'w') as f:
				f.truncate(0)

def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
	logger = logging.getLogger(name)
	
	if not logger.handlers:
		logger.setLevel(level)
		
		file_handler = logging.FileHandler(log_file)
		file_handler.setLevel(level)
		
		formatter = logging.Formatter(
			"%(asctime)s | %(levelname)-8s | %(message)s",
			datefmt="%Y-%m-%d %H:%M:%S"
		)
		file_handler.setFormatter(formatter)
		
		logger.addHandler(file_handler)
		logger.propagate = False
	
	return logger

api_logger = None
error_logger = None
slow_logger = None

def initialize_loggers():
	global api_logger, error_logger, slow_logger, _logger_initialized
	
	if not _logger_initialized:
		clear_log_files()
		
		api_logger = setup_logger("api.api", "logs/api.log")
		error_logger = setup_logger("api.error", "logs/error.log", level=logging.ERROR)
		slow_logger = setup_logger("api.slow", "logs/slow.log")
		
		api_logger.info("Logging system initialized - logs cleared")
		_logger_initialized = True
	
	return api_logger, error_logger, slow_logger

class LoggingMiddleware(BaseHTTPMiddleware):
	async def dispatch(
		self, request: Request, call_next: RequestResponseEndpoint
	):
		global api_logger, error_logger, slow_logger
		
		if api_logger is None:
			api_logger, error_logger, slow_logger = initialize_loggers()
		
		start_time = time.time()
		method = request.method
		
		full_url = request.url.path
		if request.query_params:
			full_url += f"?{request.query_params}"
		
		try:
			response = await call_next(request)
			
			process_time = time.time() - start_time
			process_time_ms = int(process_time * 1000)
			
			status_code = response.status_code
			
			log_msg = f"{method} {full_url} | Status: {status_code} | Time: {process_time_ms}ms"
			
			api_logger.info(log_msg)
			
			if process_time_ms > 300:
				slow_logger.info(f"{method} {full_url} | Status: {status_code} | Time: {process_time_ms}ms")
				
			return response
			
		except Exception as e:
			process_time = time.time() - start_time
			process_time_ms = int(process_time * 1000)
			
			error_msg = f"{method} {full_url} | Error: {str(e)} | Time: {process_time_ms}ms"
			error_logger.error(error_msg)
			api_logger.error(error_msg)
			
			raise

def init_app_logging(app: FastAPI) -> None:
	global api_logger, error_logger, slow_logger
	
	api_logger, error_logger, slow_logger = initialize_loggers()
	app.add_middleware(LoggingMiddleware)
	api_logger.info("Logging middleware initialized")