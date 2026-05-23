"""Step 2: verify all Gerby template files are present in the installed package."""
import importlib.resources
from pathlib import Path

import pytest

EXPECTED_TEMPLATES = [
    "Alignment.jinja2s",
    "Bibliography.jinja2s",
    "Breaking.jinja2s",
    "Crossref.jinja2s",
    "Diagrams.jinja2s",
    "FontSelection.jinja2s",
    "Footnotes.jinja2s",
    "Lists.jinja2s",
    "Math.jinja2s",
    "Misc.jinja2s",
    "Primitives.jinja2s",
    "Quotations.jinja2s",
    "Sectioning.jinja2s",
    "Sentences.jinja2s",
    "Thms.jinja2s",
    "Verbatim.jinja2s",
]


def _gerby_renderer_dir() -> Path:
    import plastex_gerby.Renderers.Gerby as pkg
    return Path(pkg.__file__).parent


@pytest.mark.parametrize("template", EXPECTED_TEMPLATES)
def test_template_file_present(template):
    path = _gerby_renderer_dir() / template
    assert path.exists(), f"Missing template file: {template}"
    assert path.stat().st_size > 0, f"Template file is empty: {template}"


def test_all_templates_accounted_for():
    """No extra unexpected .jinja2s files have crept in."""
    gerby_dir = _gerby_renderer_dir()
    found = {p.name for p in gerby_dir.glob("*.jinja2s")}
    expected = set(EXPECTED_TEMPLATES)
    assert found == expected, (
        f"Unexpected templates: {found - expected}\n"
        f"Missing templates: {expected - found}"
    )
