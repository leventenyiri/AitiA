import time
import logging
import logging.config
import logging.handlers
from functools import wraps


def log_execution_time(operation_name=None):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = end_time - start_time

            if operation_name:
                log_message = f"{operation_name} ({func.__name__}) took {execution_time:.6f} seconds"
            else:
                log_message = f"{func.__name__} took {execution_time:.6f} seconds"

            logging.info(log_message)
            return result
        return wrapper
    return decorator
