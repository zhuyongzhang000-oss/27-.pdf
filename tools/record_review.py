"""Record a completed visual review and refresh the public chapter index."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--title", required=True)
    p.add_argument("--printed-start", type=int, required=True)
    p.add_argument("--printed-end", type=int, required=True)
    p.add_argument("--pdf-start", type=int, required=True)
    p.add_argument("--pdf-end", type=int, required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--exception", action="append", default=[])
    args = p.parse_args()
    progress_path = ROOT / "tools/note-progress.json"
    plan_path = ROOT / "tools/chapter-plan.json"
    progress = json.loads(progress_path.read_text(encoding="utf-8"))
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert args.file in [c["file"] for c in plan], "Unknown chapter file"
    text = (ROOT / args.file).read_text(encoding="utf-8")
    assert text.splitlines()[0] == "# " + args.title
    assert "\u200b" not in text and "\ufffd" not in text
    assert not any(ad in text for ad in ["扫码打印", "首单免费", "继续前进，冲冲冲"])
    for chapter in progress["completed_chapters"]:
        if chapter["file"] != args.file:
            assert digest(ROOT / chapter["file"]) == chapter["sha256"], f"Reviewed file changed: {chapter['file']}"
    item = {"file": args.file, "title": args.title,
            "printed_pages": list(range(args.printed_start, args.printed_end+1)),
            "source_pdf_pages_reviewed": list(range(args.pdf_start, args.pdf_end+1)),
            "start_boundary": args.start, "end_boundary": args.end,
            "visual_review": True, "tables_expanded": True,
            "advertisements_headers_footers_removed": True,
            "ocr_differences_checked": args.exception,
            "sha256": digest(ROOT / args.file)}
    progress["completed_chapters"] = [c for c in progress["completed_chapters"] if c["file"] != args.file] + [item]
    order = {c["file"]: i for i, c in enumerate(plan)}
    progress["completed_chapters"].sort(key=lambda c: order[c["file"]])
    complete = {c["file"] for c in progress["completed_chapters"]}
    for chapter in plan:
        chapter["complete"] = chapter["file"] in complete
    save(progress_path, progress)
    save(plan_path, plan)
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8").split("| 板块 |")[0]
    text += "| 板块 | 原书章节 | 印刷起始页 | 文件 | 状态 |\n|---|---|---|---|---|\n"
    for c in plan:
        name = Path(c["file"]).name
        link = f"[{name}]({c['file']})" if c["complete"] else name
        text += f"| {c['block']} | {c['title_from_contents']} | {c['start_printed_page']} | {link} | {'已核对' if c['complete'] else '待完成'} |\n"
    readme.write_text(text, encoding="utf-8")
    print(f"Recorded {args.file}; {len(complete)}/{len(plan)} chapters reviewed")
