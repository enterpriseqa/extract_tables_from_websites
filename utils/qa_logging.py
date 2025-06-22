import logging
import threading

# --- Setup ---

# 1. Configure a logger (you might have this setup elsewhere in your app)
# Using a named logger is good practice
logger = logging.getLogger('qa_logging')
logger.setLevel(logging.DEBUG)  # Set the desired level

# Add a handler if none exist (e.g., for basic script usage)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(threadName)s - [%(levelname)s] - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

# 2. Create thread-local storage
# This object's attributes are specific to each thread
_thread_local_data = threading.local()

# --- Utility Functions ---


def set_thread_context_id(context_id: any):  # type: ignore
    """
    Stores a context ID specifically for the *currently executing* thread.

    This ID can be retrieved later within the same thread, typically for logging.

    Args:
        context_id: The identifier to associate with the current thread's context.
                    Can be any type (string, int, etc.).
    """
    _thread_local_data.context_id = context_id
    # Optional: Log the setting itself for debugging
    # logger.debug(f"Context ID '{context_id}' set for thread {threading.current_thread().name}")


def get_thread_context_id() -> any:  # type: ignore
    """
    Retrieves the context ID associated with the *currently executing* thread.

    Returns:
        The stored context ID, or None if no ID has been set for this thread.
    """
    thread_context_id = getattr(_thread_local_data, 'context_id', None)
    if (thread_context_id is None):
        raise Exception("invalid thread_context_id")
    return thread_context_id


def clear_thread_context_id():
    """
    Removes the context ID from the *currently executing* thread's context.

    Good practice to call this when the context is no longer valid (e.g., thread task ends).
    """
    if hasattr(_thread_local_data, 'context_id'):
        # Optional: Log the clearing for debugging
        # removed_id = _thread_local_data.context_id
        # logger.debug(f"Context ID '{removed_id}' cleared for thread {threading.current_thread().name}")
        del _thread_local_data.context_id


def log_message(log_data: str, level: int = logging.DEBUG, **kwargs):
    """
    Logs a message using the configured logger, automatically prepending
    the current thread's context ID if it exists.

    Args:
        log_data: The main message string to log.
        level: The logging level (e.g., logging.INFO, logging.DEBUG).
        **kwargs: Additional keyword arguments passed directly to the logger
                  (e.g., exc_info=True).
    """
    context_id = get_thread_context_id()

    if context_id is not None:
        # Prepend the context ID to the message
        formatted_message = f"[CtxID: {context_id}] {log_data}"
    else:
        # Log without the context ID prefix
        formatted_message = log_data

    logger.log(level, formatted_message, **kwargs)
