"""
Verify that TikZ and tikz-cd environments are passed through as raw XML tags
in the Gerby renderer output. Gerby does not compile TikZ to images; it
outputs the LaTeX source wrapped in <tikzpicture>/<tikzcd> tags for the
Gerby web application to handle.
"""
import os
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).parent
EXTRAS = HERE / "gerby_rendering/extras"

TEX_WITH_TIKZ = r"""
\documentclass{article}
\usepackage{amsthm}
\usepackage{tikz}
\usepackage{tikz-cd}

\newtheorem{theorem}{Theorem}[section]

\begin{document}

\section{Diagrams}

\begin{theorem}
\label{thm:diagram}
Consider the following commutative diagram:
\begin{tikzcd}
    A \ar[r, "f"] \ar[dr, "h"'] & B \ar[d, "g"] \\
                                 & C
\end{tikzcd}
\end{theorem}

\begin{proof}
The triangle commutes. Here is a TikZ picture:
\begin{tikzpicture}
    \draw (0,0) -- (1,0) -- (0.5,1) -- cycle;
\end{tikzpicture}
\end{proof}

\end{document}
""".strip()

TAGS = "0042,thm:diagram\n"


def _render_tikz(tmpdir: Path) -> None:
    from plasTeX.Config import defaultConfig
    from plasTeX.TeX import TeX, TeXDocument

    from plastex_gerby.Renderers.Gerby import Renderer
    from plastex_gerby.Renderers.Gerby.Config import addConfig

    config = defaultConfig()
    addConfig(config)
    config["gerby"]["tags"] = "tags"

    (tmpdir / "input.tex").write_text(TEX_WITH_TIKZ)
    (tmpdir / "tags").write_text(TAGS)

    doc = TeXDocument(config=config)
    tex = TeX(doc)
    tex.input(TEX_WITH_TIKZ)
    parsed = tex.parse()
    parsed.userdata["working-dir"] = str(tmpdir)

    old = os.getcwd()
    os.chdir(tmpdir)
    try:
        Renderer().render(parsed)
    finally:
        os.chdir(old)


def test_tikzcd_passed_through_as_raw_tag(tmp_path):
    _render_tikz(tmp_path)

    tag_files = list(tmp_path.glob("*.tag"))
    assert tag_files, "No .tag files produced"

    content = tag_files[0].read_text()
    assert "<tikzcd" in content, (
        "Expected <tikzcd> passthrough tag in .tag output, got:\n" + content
    )


def test_tikzpicture_passed_through_as_raw_tag(tmp_path):
    _render_tikz(tmp_path)

    proof_files = list(tmp_path.glob("*.proof"))
    assert proof_files, "No .proof files produced"

    content = proof_files[0].read_text()
    assert "<tikzpicture" in content, (
        "Expected <tikzpicture> passthrough tag in .proof output, got:\n" + content
    )


def test_no_image_files_generated(tmp_path):
    """Gerby does not compile TikZ to images; the imager should not run."""
    _render_tikz(tmp_path)

    image_files = list(tmp_path.glob("images/*"))
    assert not image_files, (
        "Unexpected image files generated (Gerby should pass TikZ through raw): "
        + str(image_files)
    )
