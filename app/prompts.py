from jinja2 import Environment, FileSystemLoader

from .utils.paths import resource_path


def render_template(template_name: str, content: str) -> str:
    """Render the prompt using the specified Jinja2 template."""
    env = Environment(loader=FileSystemLoader(resource_path("templates")))
    template = env.get_template(f"{template_name}.j2")
    return template.render(content=content)
