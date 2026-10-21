"""Flag source OCR lines absent from reviewed notes; never auto-correct the book."""
from pathlib import Path
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[1]


def normalize(text):
    return "".join(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]", text))


def audit(note, first, last, first_y=140, last_y=1450):
    text = normalize((ROOT / note).read_text(encoding="utf-8"))
    findings = []
    for n in range(first, last+1):
        data = json.loads((ROOT / "ai-materials/ocr/pages" / f"p{n:04d}.json").read_text(encoding="utf-8"))
        for line in data["lines"]:
            xs = [p[0] for p in line["box"]]
            ys = [p[1] for p in line["box"]]
            low = first_y if n == first else 140
            high = last_y if n == last else 1450
            if min(ys) < low or max(ys) > high or max(xs) < 100:
                continue
            source = line["text"]
            if any(t in source for t in ["理论内容", "命题思路", "理解部分", "背诵部分", "第一部分", "第二部分", "第三部分", "第四部分", "第五部分"]):
                continue
            source = re.sub(r"[（(]\s*[对错]\s*[）)]", "", source)
            clean = normalize(source)
            clean = re.sub(r"^\d+", "", clean)
            if len(clean) < 6:
                continue
            if clean not in text:
                findings.append({"pdf_page": n, "printed_page": n-9, "source_line": source,
                                 "confidence": line["confidence"], "box": line["box"]})
    return findings


if __name__ == "__main__":
    findings = audit(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]),
                     float(sys.argv[4]) if len(sys.argv)>4 else 140,
                     float(sys.argv[5]) if len(sys.argv)>5 else 1450)
    print(json.dumps(findings, ensure_ascii=False, indent=2))
