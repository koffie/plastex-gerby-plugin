"""
Generate benchmark files for functional tests by rendering fixtures with the
original gerby-project/plastex renderer.

The gerby renderer is a fork of plasTeX that has \newtheorem and \proof
built in (no \usepackage{amsthm} required). Benchmarks are generated from
benchmarks/sources/ which uses this built-in behaviour.

Run with the gerby venv:
    .venv-gerby/bin/python benchmarks/generate_benchmarks.py

Output files are written to tests/gerby_rendering/benchmarks/ and should be
committed to the repository.
"""
import importlib
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent.parent  # repo root
SOURCES = HERE / "benchmarks/sources"
EXTRAS = HERE / "tests/gerby_rendering/extras"
BENCHMARKS = HERE / "tests/gerby_rendering/benchmarks"

# Verify we're running inside the gerby venv.
try:
    from plasTeX.Renderers.Gerby import Renderer
    from plasTeX.Config import config
    from plasTeX.ConfigManager import *
    import plasTeX
    from plasTeX.TeX import TeX
except ImportError as e:
    sys.exit(f"ERROR: must run with the gerby venv (.venv-gerby). Import failed: {e}")


def collect_renderer_config(cfg):
    plastex_dir = Path(plasTeX.__file__).parent
    renderers_dir = plastex_dir / "Renderers"
    for renderer in os.listdir(renderers_dir):
        try:
            conf = importlib.import_module(f"plasTeX.Renderers.{renderer}.Config")
        except ImportError:
            continue
        cfg += conf.config


def render_tex(tex_path: Path, tags_path: Path, outdir: Path) -> None:
    collect_renderer_config(config)
    config["general"]["renderer"] = "Gerby"
    config["gerby"]["tags"] = "tags"

    document = plasTeX.TeXDocument(config=config)
    tex = TeX(document, myfile=str(tex_path))
    document.userdata["working-dir"] = str(outdir)

    shutil.copy(str(tags_path), str(outdir / "tags"))

    doc = tex.parse()
    doc.userdata["working-dir"] = str(outdir)

    old_cwd = os.getcwd()
    os.chdir(outdir)
    try:
        Renderer().render(doc)
    finally:
        os.chdir(old_cwd)


def main():
    BENCHMARKS.mkdir(parents=True, exist_ok=True)

    for src in sorted(SOURCES.glob("*.tex")):
        print(f"Rendering {src.name} ...")
        tags = EXTRAS / "tags"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            shutil.copy(src, tmpdir / src.name)

            render_tex(tmpdir / src.name, tags, tmpdir)

            output_files = list(tmpdir.glob("*.tag")) + list(tmpdir.glob("*.proof"))
            if not output_files:
                print(f"  WARNING: no .tag or .proof files produced for {src.name}")
            for f in sorted(output_files):
                dest = BENCHMARKS / f.name
                shutil.copy(f, dest)
                print(f"  -> benchmarks/{f.name}")

    print("Done.")


if __name__ == "__main__":
    main()
