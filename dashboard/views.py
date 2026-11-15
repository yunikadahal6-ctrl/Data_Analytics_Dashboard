"""Page views for the dashboard app."""

from django.contrib import messages
from django.db import connection, transaction
from django.db.models import Count, DecimalField, F, Sum
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import SaleFilterForm, SalesCSVUploadForm
from .models import Sale


def home(request, upload_form=None, status=200):
    """Display sales summaries and records stored in the database."""
    sales = Sale.objects.all()
    filter_form = SaleFilterForm(request.GET or None)
    if filter_form.is_bound and filter_form.is_valid():
        if filter_form.cleaned_data["product"]:
            sales = sales.filter(product=filter_form.cleaned_data["product"])
        if filter_form.cleaned_data["region"]:
            sales = sales.filter(region=filter_form.cleaned_data["region"])

    totals = sales.aggregate(
        total_revenue=Sum(
            F("quantity") * F("unit_price"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        ),
        total_orders=Count("id"),
        total_quantity=Sum("quantity"),
    )
    best_seller = (
        sales.values("product")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("-total_quantity", "product")
        .first()
    )
    product_sales = list(
        sales.values("product")
        .annotate(units_sold=Sum("quantity"))
        .order_by("product")
    )
    region_sales = list(
        sales.values("region")
        .annotate(units_sold=Sum("quantity"))
        .order_by("region")
    )
    daily_sales = list(
        sales.values("date")
        .annotate(units_sold=Sum("quantity"))
        .order_by("date")
    )

    context = {
        "upload_form": upload_form or SalesCSVUploadForm(),
        "filter_form": filter_form,
        "sales": sales,
        "total_revenue": totals["total_revenue"] or 0,
        "total_orders": totals["total_orders"],
        "total_quantity": totals["total_quantity"] or 0,
        "best_selling_product": best_seller["product"] if best_seller else "No sales yet",
        "best_selling_quantity": best_seller["total_quantity"] if best_seller else 0,
        "chart_data": {
            "products": {
                "labels": [sale["product"] for sale in product_sales],
                "values": [sale["units_sold"] for sale in product_sales],
            },
            "regions": {
                "labels": [sale["region"] for sale in region_sales],
                "values": [sale["units_sold"] for sale in region_sales],
            },
            "daily_sales": {
                "labels": [sale["date"].isoformat() for sale in daily_sales],
                "values": [sale["units_sold"] for sale in daily_sales],
            },
        },
    }
    return render(request, "dashboard/home.html", context, status=status)


@require_POST
def upload_sales(request):
    """Validate and import sales from an uploaded CSV file."""
    form = SalesCSVUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return home(request, upload_form=form, status=400)

    sales = form.cleaned_data["sales"]
    with transaction.atomic():
        existing_rows = set(
            Sale.objects.values_list("date", "product", "region", "quantity", "unit_price")
        )
        duplicate = next(
            (
                sale
                for sale in sales
                if (sale.date, sale.product, sale.region, sale.quantity, sale.unit_price)
                in existing_rows
            ),
            None,
        )
        if duplicate is not None:
            form.add_error(
                "csv_file",
                f"Row {duplicate.csv_row_number} matches a sale already in the database. "
                "No rows were imported.",
            )
            return home(request, upload_form=form, status=400)

        Sale.objects.bulk_create(sales)

    messages.success(request, f"Imported {len(sales)} sales records successfully.")
    return redirect("dashboard:home")


def sql_practice(request):
    """Run and display a few read-only SQL examples against the sales table."""
    examples = [
        {
            "title": "WHERE: filter rows",
            "explanation": "Show only sales from the East region.",
            "sql": "SELECT date, product, region, quantity\n"
            "FROM dashboard_sale\n"
            "WHERE region = 'East';",
        },
        {
            "title": "ORDER BY: sort rows",
            "explanation": "List sales from highest to lowest unit price.",
            "sql": "SELECT product, unit_price\n"
            "FROM dashboard_sale\n"
            "ORDER BY unit_price DESC;",
        },
        {
            "title": "GROUP BY: group matching values",
            "explanation": "Count how many sale records there are for each product.",
            "sql": "SELECT product, COUNT(*) AS sale_count\n"
            "FROM dashboard_sale\n"
            "GROUP BY product\n"
            "ORDER BY product;",
        },
        {
            "title": "SUM and COUNT: aggregate the whole table",
            "explanation": "Add all quantities and count all sale records.",
            "sql": "SELECT SUM(quantity) AS units_sold, COUNT(*) AS sale_count\n"
            "FROM dashboard_sale;",
        },
    ]

    for example in examples:
        with connection.cursor() as cursor:
            cursor.execute(example["sql"])
            example["columns"] = [column[0] for column in cursor.description]
            example["rows"] = cursor.fetchall()

    return render(request, "dashboard/sql_practice.html", {"examples": examples})
