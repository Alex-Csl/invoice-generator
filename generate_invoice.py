#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import csv
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

try:
    from weasyprint import CSS, HTML
except ImportError as e:
    sys.exit("WeasyPrint is not installed. Run: pip install weasyprint jinja2\n" + str(e))

try:
    from jinja2 import Environment, FileSystemLoader
    JINJA = True
except ImportError:
    JINJA = False


BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
TPL = BASE / "templates"
OUT = BASE / "output"
OUT.mkdir(exist_ok=True)

ID_KEYS = {
    "invoice_id",
    "invoice",
    "id",
    "invoice_number",
    "number",
    "check_number",
}

BASE_CSS = """
@page { size: A4; margin: 18mm 14mm; }
body { font-family: "DejaVu Sans", "Roboto", Arial, sans-serif; font-size: 12px; }
table { width: 100%; border-collapse: collapse; margin-top: 12px; }
th, td { border: 1px solid #999; padding: 6px 8px; text-align: left; }
th { background: #f2f2f2; }
"""


def font_css():
    fp = os.getenv("PDF_FONT_PATH")
    if fp and Path(fp).is_file():
        uri = Path(fp).as_uri()
        return f"""
@font-face {{ font-family: "DejaVu Sans"; src: url("{uri}"); }}
body, table, th, td {{ font-family: "DejaVu Sans", "Roboto", Arial, sans-serif; }}
"""
    return ""


def list_files(dir_path, exts):
    if not dir_path.is_dir():
        return []
    return sorted(
        p for p in dir_path.iterdir()
        if p.is_file() and p.suffix.lower() in exts
    )


def choose(title, items):
    print("\n" + title)
    for i, name in enumerate(items, 1):
        print(f"{i}. {name}")

    while True:
        raw = input(f"Выбор (1-{len(items)}, 0 выход): ").strip()
        if raw in {"0", "q", "exit", "выход"}:
            sys.exit(0)
        if raw.isdigit() and 1 <= int(raw) <= len(items):
            return int(raw) - 1
        print("Некорректный ввод")


def normalize(key):
    return str(key).strip().lower().replace(" ", "_").replace("-", "_")


def get_id(row):
    if not isinstance(row, dict):
        return None

    norm = {normalize(k): v for k, v in row.items()}

    for key in ID_KEYS:
        value = norm.get(key)
        if value not in (None, ""):
            return str(value).strip()

    for key, value in norm.items():
        if "invoice" in key and value not in (None, ""):
            return str(value).strip()

    return None


def load(path):
    if path.suffix.lower() == ".csv":
        with open(path, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))

        for row in rows:
            if isinstance(row.get("items"), str):
                try:
                    row["items"] = json.loads(row["items"])
                except Exception:
                    pass

        return rows

    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)

    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]

    if isinstance(data, dict):
        for key in ("invoices", "items", "data", "records", "rows"):
            value = data.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
        return [data]

    return []


def build_context(row, invoice_id):
    ctx = {
        "invoice": row,
        "invoice_id": invoice_id,
        "items": [],
    }

    for key, value in row.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            ctx[str(key)] = "" if value is None else value

    for key in ("items", "positions", "products", "lines"):
        value = row.get(key)
        if isinstance(value, list):
            ctx["items"] = value
            break

    return ctx


def render(template_path, ctx):
    if JINJA:
        env = Environment(
            loader=FileSystemLoader(str(template_path.parent)),
            autoescape=True,
        )
        return env.get_template(template_path.name).render(ctx)

    text = template_path.read_text(encoding="utf-8")

    for key, value in ctx.items():
        if isinstance(value, (dict, list)):
            continue

        value = "" if value is None else str(value)
        text = text.replace("{{ " + key + " }}", value)
        text = text.replace("{{" + key + "}}", value)

    return text


def open_file(path):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        print("Не удалось открыть файл автоматически:", e)


def main():
    data_files = list_files(DATA, {".csv", ".json"})
    tpl_files = list_files(TPL, {".html", ".htm"})

    if not data_files:
        sys.exit("Нет файлов данных в папке data/")

    if not tpl_files:
        sys.exit("Нет HTML-шаблонов в папке templates/")

    data_index = choose("Доступные файлы данных", [p.name for p in data_files])
    tpl_index = choose("Доступные шаблоны", [p.name for p in tpl_files])

    rows = load(data_files[data_index])

    invoices = []
    for row in rows:
        invoice_id = get_id(row)
        if invoice_id:
            invoices.append((invoice_id, row))

    if not invoices:
        sys.exit("Не найден invoice id в файле данных")

    invoice_index = choose("Доступные чеки / invoice id", [x[0] for x in invoices])
    invoice_id, row = invoices[invoice_index]

    html = render(tpl_files[tpl_index], build_context(row, invoice_id))

    safe_id = "".join(
        c if c.isalnum() or c in "-_" else "_" for c in invoice_id
    )

    pdf_path = OUT / f"{safe_id}.pdf"

    HTML(
        string=html,
        base_url=str(tpl_files[tpl_index].parent),
    ).write_pdf(
        str(pdf_path),
        stylesheets=[CSS(string=BASE_CSS + font_css())],
    )

    print("PDF создан:", pdf_path)
    open_file(str(pdf_path))


if __name__ == "__main__":
    main()
