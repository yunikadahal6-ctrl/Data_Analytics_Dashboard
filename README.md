# Data Analytics Dashboard

A Django sales analytics dashboard for exploring sample sales data, importing CSV files, filtering results, and practicing read-only SQL.

## Features

- Sales summary cards for revenue, order count, quantity, and best-selling product
- Responsive charts for product, region, and daily sales
- Product and region filters that update summaries, charts, and records
- Validated CSV import with duplicate detection and row/file limits
- SQL practice examples with results from the local sales database
- Starter data loaded by the initial app migrations

## Tech stack

- Python 3.12+ and Django 5.2
- SQLite
- HTML, CSS, JavaScript, and Chart.js 4 (loaded from jsDelivr)

## Setup

1. Create and activate a virtual environment:

   ```powershell
   py -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. Install Django:

   ```powershell
   python -m pip install "Django>=5.2,<5.3"
   ```

3. Apply migrations and run the development server:

   ```powershell
   python manage.py migrate
   python manage.py runserver
   ```

4. Open http://127.0.0.1:8000/.

## CSV format

CSV files must include `date`, `product`, `region`, `quantity`, and `unit_price` columns. UTF-8 CSV files up to 5 MB and 10,000 sales rows are accepted. A sample is available at `dashboard/data/sample_sales.csv`.

## Screenshots

### Dashboard overview

![Data Analytics Dashboard overview](screenshots/Dashboard.png)

### Chart detail

![Sales chart detail](screenshots/chart.png)

### Sales charts

![Sales analytics charts](screenshots/charts.png)

### CSV import

![CSV sales import interface](screenshots/csv.png)

### Sales filters

![Product and region sales filters](screenshots/filter_sales.png)

Add screenshots here before publishing:

- **Dashboard:** `docs/screenshots/dashboard.png`
- **SQL practice:** `docs/screenshots/sql-practice.png`

## Checks

```powershell
python manage.py check
python manage.py test
```

## GitHub notes

The local SQLite database and virtual environment are intentionally excluded from Git. Keep `SECRET_KEY` and `DEBUG` development settings out of production; configure environment-specific settings before deployment.
