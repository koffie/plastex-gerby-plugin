"""
Functional tests: render fixture .tex files with our Gerby plugin and compare
output against benchmark files produced by the original koffie/gerby-project
renderer (see scripts/generate_benchmarks.py).
"""
import re
import shutil
from pathlib import Path

import pytest

HERE = Path(__file__).parent
SOURCES = HERE / "sources"
EXTRAS = HERE / "extras"
BENCHMARKS = HERE / "benchmarks"


def _normalise(text: str) -> str:
    """Strip auto-generated ids before comparison so non-deterministic node
    ids (e.g. id="a0000000003") don't cause spurious failures."""
    return re.sub(r'\s*id="a[0-9]+"', "", text).strip()


def _render(src: Path, tmpdir: Path) -> None:
    from plasTeX.Config import defaultConfig
    from plasTeX.TeX import TeX, TeXDocument

    from plastex_gerby.Renderers.Gerby import Renderer
    from plastex_gerby.Renderers.Gerby.Config import addConfig

    config = defaultConfig()
    addConfig(config)
    config["gerby"]["tags"] = "tags"
    config["files"]["split-level"] = -2

    shutil.copy(src, tmpdir / src.name)
    shutil.copy(EXTRAS / "tags", tmpdir / "tags")

    doc = TeXDocument(config=config)
    tex = TeX(doc)
    tex.input((tmpdir / src.name).read_text())
    parsed = tex.parse()
    parsed.userdata["working-dir"] = str(tmpdir)

    import os
    old = os.getcwd()
    os.chdir(tmpdir)
    try:
        Renderer().render(parsed)
    finally:
        os.chdir(old)


# Collect all .tex sources automatically (same pattern as upstream FunctionalTests.py)
_sources = sorted(SOURCES.glob("*.tex"))


@pytest.mark.parametrize("src", _sources, ids=lambda p: p.stem)
def test_tag_files_match_benchmarks(src, tmp_path):
    _render(src, tmp_path)

    tag_files = sorted(tmp_path.glob("*.tag"))
    assert tag_files, f"No .tag files produced for {src.name}"

    for output_file in tag_files:
        bench_file = BENCHMARKS / output_file.name
        assert bench_file.exists(), (
            f"No benchmark for {output_file.name}. "
            f"Run scripts/generate_benchmarks.py to create it."
        )
        got = _normalise(output_file.read_text())
        expected = _normalise(bench_file.read_text())
        if got != expected:
            (HERE / "new").mkdir(exist_ok=True)
            (HERE / "new" / output_file.name).write_text(output_file.read_text())
        assert got == expected, f"Mismatch in {output_file.name}"


@pytest.mark.parametrize("src", _sources, ids=lambda p: p.stem)
def test_proof_files_match_benchmarks(src, tmp_path):
    _render(src, tmp_path)

    proof_files = sorted(tmp_path.glob("*.proof"))
    assert proof_files, f"No .proof files produced for {src.name}"

    for output_file in proof_files:
        bench_file = BENCHMARKS / output_file.name
        assert bench_file.exists(), (
            f"No benchmark for {output_file.name}. "
            f"Run scripts/generate_benchmarks.py to create it."
        )
        got = _normalise(output_file.read_text())
        expected = _normalise(bench_file.read_text())
        if got != expected:
            (HERE / "new").mkdir(exist_ok=True)
            (HERE / "new" / output_file.name).write_text(output_file.read_text())
        assert got == expected, f"Mismatch in {output_file.name}"
