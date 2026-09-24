from fastapi import templating

from common.config import settings

templates = templating.Jinja2Templates(directory=settings.templates_directory)
