import logging
from pathlib import Path

# Create logs directory
BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Configure audit logger
audit_logger = logging.getLogger("telekali.audit")
audit_logger.setLevel(logging.INFO)
audit_logger.propagate = False

# Configure file handler
if not audit_logger.handlers:
    handler = logging.FileHandler(
        LOG_DIR / "telekali.log"
    )

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )

    handler.setFormatter(formatter)
    audit_logger.addHandler(handler)


def log_execution(user_id, command, status, returncode=None):
    audit_logger.info(
        "USER=%s | COMMAND=%r | STATUS=%s | EXIT_CODE=%s",
        user_id,
        command,
        status,
        returncode,
    )
