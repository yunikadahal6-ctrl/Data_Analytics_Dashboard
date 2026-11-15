"""Add the six starter sales records to the database."""

from decimal import Decimal

from django.db import migrations


def add_sample_sales(apps, schema_editor):
    Sale = apps.get_model("dashboard", "Sale")
    Sale.objects.bulk_create(
        [
            Sale(date="2026-01-05", product="Notebook", region="East", quantity=12, unit_price=Decimal("3.50")),
            Sale(date="2026-01-08", product="Pen Set", region="West", quantity=8, unit_price=Decimal("5.25")),
            Sale(date="2026-01-12", product="Desk Lamp", region="North", quantity=3, unit_price=Decimal("24.99")),
            Sale(date="2026-01-18", product="Notebook", region="South", quantity=15, unit_price=Decimal("3.50")),
            Sale(date="2026-01-22", product="Desk Lamp", region="East", quantity=2, unit_price=Decimal("24.99")),
            Sale(date="2026-01-27", product="Pen Set", region="North", quantity=10, unit_price=Decimal("5.25")),
        ]
    )


class Migration(migrations.Migration):
    dependencies = [
        ("dashboard", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_sample_sales, migrations.RunPython.noop),
    ]
