from plasTeX.ConfigManager import ConfigManager, StringOption


def addConfig(config: ConfigManager) -> None:
    section = config.addSection('gerby', 'Gerby renderer options')

    section['tags'] = StringOption(
        """Location of the tags file""",
        options='--tags',
        default='tags',
    )

    section['tikz-compiler'] = StringOption(
        """LaTeX compiler for TikZ pictures""",
        options='--tikz-compiler',
        default='pdflatex',
    )

    section['tikz-converter'] = StringOption(
        """PDF to SVG converter for tikz and tikz-cd""",
        options='--tikz-converter',
        default='pdf2svg',
    )

    section['tikz-template'] = StringOption(
        """Jinja2 template file for tikz""",
        options='--tikz-template',
        default='',
    )

    section['tikz-cd-template'] = StringOption(
        """Jinja2 template file for tikz-cd""",
        options='--tikz-cd-template',
        default='',
    )
