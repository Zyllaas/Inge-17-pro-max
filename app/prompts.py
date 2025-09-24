from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from pathlib import Path

from .utils.paths import resource_path


class TemplateManager:
    def __init__(self):
        self.templates_dir = resource_path("templates")
        self.env = Environment(loader=FileSystemLoader(self.templates_dir))

    def render_template(self, template_name: str, content: str) -> str:
        """Render the prompt using the specified Jinja2 template."""
        try:
            template_file = f"{template_name}.j2"
            template = self.env.get_template(template_file)
            return template.render(content=content)
        except TemplateNotFound:
            print(f"Template {template_name}.j2 not found, using content as-is")
            return content
        except Exception as e:
            print(f"Error rendering template {template_name}: {e}")
            return content

    def list_templates(self) -> list[str]:
        """List available templates."""
        try:
            templates_path = Path(self.templates_dir)
            if templates_path.exists():
                return [f.stem for f in templates_path.glob("*.j2")]
            return []
        except Exception as e:
            print(f"Error listing templates: {e}")
            return []

    def template_exists(self, template_name: str) -> bool:
        """Check if a template exists."""
        try:
            template_file = f"{template_name}.j2"
            self.env.get_template(template_file)
            return True
        except TemplateNotFound:
            return False
        except Exception:
            return False
