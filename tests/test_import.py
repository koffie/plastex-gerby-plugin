"""Step 1: verify the package structure is importable."""


def test_renderer_importable():
    from plastex_gerby.Renderers.Gerby import Renderer
    assert Renderer is not None


def test_renderer_is_subclass_of_page_template():
    from plasTeX.Renderers.PageTemplate import Renderer as PageTemplateRenderer
    from plastex_gerby.Renderers.Gerby import Renderer
    assert issubclass(Renderer, PageTemplateRenderer)


def test_renderer_has_correct_file_extension():
    from plastex_gerby.Renderers.Gerby import Renderer
    assert Renderer.fileExtension == '.tag'
