# Invoice Generator

## Установка зависимостей

    python -m pip install --upgrade pip
    python -m pip install weasyprint jinja2

Для Windows также может потребоваться GTK3 Runtime:

https://github.com/tschoonhoven/GTK-for-Windows-Runtime-Environment-Installer/releases

## Запуск

    python generate_invoice.py

Если команда python не работает, используйте:

    py generate_invoice.py

## Структура

    invoice_generator/
    |-- generate_invoice.py
    |-- requirements.txt
    |-- README.md
    |-- data/
    |   |-- invoices.csv
    |   |-- orders.json
    |-- templates/
    |   |-- invoice_template.html
    |-- output/

PDF файлы создаются в папке output.
