import logging
from config import settings

def setup_logging():
    log_level = logging.INFO if settings.APP_ENV == "local" else logging.WARNING
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(), # Output to console
            logging.FileHandler("app.log") # Output to file
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()
