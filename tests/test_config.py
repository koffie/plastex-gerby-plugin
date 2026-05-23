"""Step 3: verify the Gerby config section integrates correctly with upstream plasTeX."""
import pytest
from plasTeX.Config import defaultConfig


@pytest.fixture
def config():
    from plastex_gerby.Renderers.Gerby.Config import addConfig
    cfg = defaultConfig()
    addConfig(cfg)
    return cfg


def test_gerby_section_exists(config):
    assert 'gerby' in config


def test_default_tags(config):
    assert config['gerby']['tags'] == 'tags'


def test_default_tikz_compiler(config):
    assert config['gerby']['tikz-compiler'] == 'pdflatex'


def test_default_tikz_converter(config):
    assert config['gerby']['tikz-converter'] == 'pdf2svg'


def test_default_tikz_template(config):
    assert config['gerby']['tikz-template'] == ''


def test_default_tikz_cd_template(config):
    assert config['gerby']['tikz-cd-template'] == ''


def test_all_expected_keys_present(config):
    expected = {'tags', 'tikz-compiler', 'tikz-converter', 'tikz-template', 'tikz-cd-template'}
    actual = set(config['gerby'].data.keys())
    assert actual == expected


def test_tags_option_is_overridable(config):
    config['gerby']['tags'] = 'mytags'
    assert config['gerby']['tags'] == 'mytags'
