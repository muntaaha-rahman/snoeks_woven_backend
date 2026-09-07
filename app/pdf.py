from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.config import settings

TEMPLATES_DIR = Path(__file__).parent / "templates"
_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))


def render_visit_pdf(visit_dict: dict) -> bytes:
    template = _env.get_template("report.html")
    html = template.render(visit=visit_dict, company_name=settings.company_name)
    return HTML(string=html).write_pdf()
