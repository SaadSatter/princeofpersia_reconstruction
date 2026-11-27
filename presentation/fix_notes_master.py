"""Make a python-pptx deck with speaker notes importable by Keynote.

python-pptx adds a notes master part and a relationship to it, but never writes the
`<p:notesMasterIdLst>` element in ppt/presentation.xml that lists it. PowerPoint tolerates that;
Keynote does not (open returns no document). This post-processor adds the element, nothing else.

    python3 presentation/fix_notes_master.py DECK.pptx
"""

from __future__ import annotations

import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

NOTES_MASTER_TYPE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesMaster"


def fix(path: Path) -> bool:
    """Add the missing notesMasterIdLst. Returns True if the package was changed."""
    with zipfile.ZipFile(path) as z:
        pres = z.read("ppt/presentation.xml").decode("utf8")
        rels = z.read("ppt/_rels/presentation.xml.rels").decode("utf8")
        if "notesMasterIdLst" in pres:
            return False
        m = re.search(r'<Relationship [^>]*Id="([^"]+)"[^>]*Type="%s"' % re.escape(NOTES_MASTER_TYPE), rels) \
            or re.search(r'<Relationship [^>]*Type="%s"[^>]*Id="([^"]+)"' % re.escape(NOTES_MASTER_TYPE), rels)
        if not m:
            return False                      # no notes in this deck
        new = pres.replace("</p:sldMasterIdLst>",
                           '</p:sldMasterIdLst><p:notesMasterIdLst><p:notesMasterId r:id="%s"/></p:notesMasterIdLst>' % m.group(1), 1)
        assert new != pres
        tmp = Path(tempfile.mkstemp(suffix=".pptx")[1])
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
            for item in z.infolist():
                data = z.read(item.filename)
                if item.filename == "ppt/presentation.xml":
                    data = new.encode("utf8")
                out.writestr(item, data)
    shutil.move(str(tmp), path)
    return True


if __name__ == "__main__":
    print("fixed" if fix(Path(sys.argv[1])) else "unchanged")
