import json
import os
import re
import shutil

import plasTeX
from plasTeX.DOM import Node
from plasTeX.Renderers import Renderable, mixin, unmix
from plasTeX.Renderers.PageTemplate import Renderer as _Renderer

log = plasTeX.Logging.getLogger()


def searchPrecedingTheorem(linear, node):
    """Return the id of the closest preceding thmenv node in the linear list."""
    last = None
    for current in linear:
        if current.nodeName == "thmenv":
            last = current
        if current.isSameNode(node):
            return last.id


def willItBeWhitespace(node):
    if node.isElementContentWhitespace:
        return True
    elif node.nodeName in ["label", "reference", "slogan", "history"]:
        return True
    elif node.nodeName == "par":
        return all(willItBeWhitespace(child) for child in node.childNodes)


class GerbyRenderable(Renderable):
    @property
    def filenameoverride(self):
        # Tagged theorems/environments -> {env}-{ref}-{tag}-{id}.tag
        if "tag" in self.userdata:
            environment = self.nodeName
            if self.nodeName == "thmenv":
                environment = self.thmName
                for child in self.childNodes:
                    child.isItWhitespace = willItBeWhitespace(child)
            return (
                str(environment)
                + "-" + str(self.ref)
                + "-" + str(self.userdata["tag"])
                + "-" + str(self.id)
                + ".tag"
            )

        # Proofs -> {tag}-{count}.proof
        if self.nodeName == "proof":
            caption = self.attributes.get("caption")
            if caption and caption.getElementsByTagName("ref"):
                label = caption.getElementsByTagName("ref")[0].attributes["label"]
            else:
                label = searchPrecedingTheorem(
                    self.ownerDocument.userdata["linear"], self
                )
            if label in self.ownerDocument.userdata["labels"]:
                tag = self.ownerDocument.userdata["labels"][label]
                self.ownerDocument.userdata["proofs"][tag] += 1
                return tag + "-" + str(self.ownerDocument.userdata["proofs"][tag]) + ".proof"

        # Slogans, history, references -> {tag}.{nodename}
        if self.nodeName in ["history", "slogan", "reference"]:
            parentEnv = self.parentNode
            while parentEnv.nodeName == "par":
                parentEnv = parentEnv.parentNode
            label = parentEnv.id
            if label in self.ownerDocument.userdata["labels"]:
                tag = self.ownerDocument.userdata["labels"][label]
                return tag + "." + self.nodeName

        raise AttributeError


def loadTags(document):
    """Read the tags file; populate document.userdata with tags/labels/proofs dicts."""
    tags_path = os.path.join(
        document.userdata["working-dir"],
        document.config["gerby"]["tags"],
    )
    with open(tags_path) as f:
        content = f.readlines()

    document.userdata["tags"] = {}    # tag  -> label
    document.userdata["labels"] = {}  # label -> tag
    document.userdata["proofs"] = {}  # tag  -> proof count

    for line in content:
        line = line.rstrip()
        if not line or line[0] == "#":
            continue
        tag, label = line.split(",")
        document.userdata["tags"][tag] = label
        document.userdata["labels"][label] = tag
        document.userdata["proofs"][tag] = 0


def decorateTags(node, labels):
    """Recursively attach tag userdata to labeled nodes."""
    if node.nodeType == plasTeX.Macro.ELEMENT_NODE and node.id[:2] != "a0":
        if node.nodeName != "hypertarget" and node.id in labels:
            node.userdata["tag"] = labels[node.id]
            if node.nodeName not in ["part", "chapter", "section", "subsection", "subsubsection"]:
                node.userdata["propagate"] = True

    if node.nodeName == "proof":
        node.userdata["propagate"] = True
        if not all(child.nodeName == "par" for child in node.childNodes):
            node.paragraphs()

    for child in node.childNodes:
        decorateTags(child, labels)


def linearRepresentation(document):
    """Build document.userdata['linear']: ordered list of thmenv/proof/... nodes."""
    linear = []
    stack = list(document.childNodes)
    while stack:
        node = stack.pop()
        if node.nodeName in ["thmenv", "proof", "reference", "history", "slogan"]:
            linear.append(node)
        stack.extend(node.childNodes)
    document.userdata["linear"] = list(reversed(linear))


def tagRollCall(document):
    """Return a dict mapping each tag to True/False (found in document or not)."""
    sheet = {t: False for t in document.userdata["tags"]}
    stack = list(document.childNodes)
    while stack:
        node = stack.pop()
        try:
            tag = node.userdata.get("tag")
            if tag and tag in sheet:
                sheet[tag] = True
        except Exception:
            pass
        stack.extend(node.childNodes)
    return sheet


def partsList(document):
    """Build a mapping of part numbers to their contained chapter numbers."""
    parts = {}
    stack = list(document.childNodes)
    current = None
    while stack:
        node = stack.pop()
        if node.nodeName == "part":
            current = node.ref.source
            parts[current] = []
        elif node.nodeName == "chapter" and current is not None:
            parts[current].append(node.ref.source)
        stack.extend(node.childNodes)
    return parts


def copyBibliographies(document):
    """Copy .bib files referenced by \\bibliography commands to the build dir."""
    stack = list(document.childNodes)
    while stack:
        node = stack.pop()
        if node.nodeName == "bibliography":
            for f in node.attributes["files"].split(","):
                src = os.path.join(document.userdata["working-dir"], f + ".bib")
                shutil.copyfile(src, f + ".bib")
        stack.extend(node.childNodes)


def checkLabels(document):
    """Warn about theorem/section nodes that have no label."""
    stack = list(document.childNodes)
    while stack:
        node = stack.pop()
        if node.nodeName in ["thmenv", "chapter", "section", "subsection", "subsubsection"]:
            if node.id[:3] == "a00" and hasattr(node.ref, "source"):
                name = node.thmName if node.nodeName == "thmenv" else node.nodeName
                log.warning("%s %s does not have a label", name, node.ref.source)
        stack.extend(node.childNodes)


class Renderer(_Renderer):
    """Tag-aware Gerby renderer for plasTeX."""

    fileExtension = ""
    imageTypes = [".png", ".jpg", ".jpeg", ".gif"]
    vectorImageTypes = [".svg"]
    renderableClass = GerbyRenderable

    def loadTemplates(self, document):
        _Renderer.loadTemplates(self, document)
        document.rendererdata["gerby"] = {}
        # Gerby always renders everything into individual tag files; disable splitting.
        document.config["files"]["split-level"] = -2
        build_dir = os.getcwd()
        for resrc in document.packageResources:
            resrc.alter(
                renderer=self,
                rendererName="gerby",
                document=document,
                target=build_dir,
            )

    def processFileContent(self, document, s):
        s = _Renderer.processFileContent(self, document, s)
        for fn in document.rendererdata["gerby"].get("processFileContents", []):
            s = fn(document, s)
        s = re.compile(r"<p>\s*</p>", re.I).sub("", s)
        s = re.compile(
            r"<p>(<div class=\"equation\".*?<\/div>)<\/p>", flags=re.DOTALL
        ).sub(r"\1", s)
        return s

    def render(self, document):
        loadTags(document)
        copyBibliographies(document)
        checkLabels(document)
        decorateTags(document, document.userdata["labels"])
        linearRepresentation(document)

        for tag in (t for t, found in tagRollCall(document).items() if not found):
            log.warning("document does not contain tag %s", tag)

        parts = partsList(document)
        with open("parts.json", "w") as f:
            json.dump(parts, f)

        _Renderer.render(self, document)

        # Write footnotes as individual files
        if "footnotes" in document.userdata:
            mixin(Node, Renderer.renderableClass)
            Node.renderer = self
            for footnote in document.userdata["footnotes"]:
                with open("{}.footnote".format(footnote.id), "w") as f:
                    f.write(str(footnote))
            del Node.renderer
            unmix(Node, Renderer.renderableClass)

        meta = getattr(document.context, "meta", {})
        with open("meta.statistics", "w") as f:
            json.dump(meta, f)
