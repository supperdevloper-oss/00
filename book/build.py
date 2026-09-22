# -*- coding: utf-8 -*-
"""يبني الكتاب كاملاً من ملفات content/ إلى PDF واحد."""
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import build  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "output")
CONTENT = os.path.join(HERE, "content")

TITLE = "مشروعي الأول فالمغرب"
AUTHOR = "دليل عملي للمبتدئين في المغرب"


def main():
    files = sorted(glob.glob(os.path.join(CONTENT, "*.md")))
    if not files:
        print("لا توجد ملفات محتوى")
        return 1
    os.makedirs(OUT_DIR, exist_ok=True)
    out = os.path.join(OUT_DIR, "meshrooi-awal-f-alma.pdf")
    pages = build(out, files, TITLE, AUTHOR)
    size = os.path.getsize(out)
    print("files:", len(files))
    print("pages:", pages)
    print("size_mb: %.2f" % (size / 1024 / 1024))
    print("out:", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
