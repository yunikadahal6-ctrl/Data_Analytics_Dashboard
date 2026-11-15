"""Forms for importing sales data."""

import csv
import io
from pathlib import Path

from django import forms
from django.core.exceptions import ValidationError

from .models import Sale


REQUIRED_COLUMNS = ("date", "product", "region", "quantity", "unit_price")
MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_ROWS = 10_000


class SalesCSVUploadForm(forms.Form):
    csv_file = forms.FileField(
        label="Sales CSV file",
        help_text="Use a .csv file with date, product, region, quantity, and unit_price columns. Maximum size: 5 MB.",
    )

    def clean_csv_file(self):
        uploaded_file = self.cleaned_data["csv_file"]
        if Path(uploaded_file.name).suffix.lower() != ".csv":
            raise forms.ValidationError("Choose a file with the .csv extension.")
        if uploaded_file.size > MAX_FILE_SIZE:
            raise forms.ValidationError("The CSV file must be 5 MB or smaller.")
        return uploaded_file

    def clean(self):
        cleaned_data = super().clean()
        uploaded_file = cleaned_data.get("csv_file")
        if uploaded_file is None:
            return cleaned_data

        try:
            text = uploaded_file.read().decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise forms.ValidationError(
                "The file must be a UTF-8 encoded CSV."
            ) from error

        reader = csv.reader(io.StringIO(text, newline=""))
        headers = next(reader, None)
        if not headers:
            raise forms.ValidationError("The CSV file is empty or has no header row.")

        normalized_headers = [header.strip().lower() for header in headers]
        if len(normalized_headers) != len(set(normalized_headers)):
            raise forms.ValidationError("The CSV header row contains duplicate column names.")

        missing_columns = [column for column in REQUIRED_COLUMNS if column not in normalized_headers]
        if missing_columns:
            missing = ", ".join(missing_columns)
            raise forms.ValidationError(f"Missing required column(s): {missing}.")

        sales = []
        seen_rows = {}
        for row_number, row in enumerate(reader, start=2):
            if not row or all(not value.strip() for value in row):
                continue
            if len(row) != len(normalized_headers):
                raise forms.ValidationError(
                    f"Row {row_number} has {len(row)} value(s), but the header has "
                    f"{len(normalized_headers)} column(s). Check for a missing or extra value."
                )
            values = dict(zip(normalized_headers, (value.strip() for value in row)))

            try:
                sale_values = {
                    field_name: Sale._meta.get_field(field_name).clean(values[field_name], None)
                    for field_name in REQUIRED_COLUMNS
                }
            except ValidationError as error:
                message = error.messages[0] if error.messages else "Invalid value."
                raise forms.ValidationError(f"Row {row_number}: {message}") from error

            key = tuple(sale_values[field_name] for field_name in REQUIRED_COLUMNS)
            if key in seen_rows:
                raise forms.ValidationError(
                    f"Row {row_number} duplicates row {seen_rows[key]} in this file."
                )
            seen_rows[key] = row_number

            sale = Sale(**sale_values)
            sale.csv_row_number = row_number
            sales.append(sale)
            if len(sales) > MAX_ROWS:
                raise forms.ValidationError(f"A CSV file can contain at most {MAX_ROWS:,} sales rows.")

        if not sales:
            raise forms.ValidationError("The CSV file does not contain any sales rows.")

        cleaned_data["sales"] = sales
        return cleaned_data


class SaleFilterForm(forms.Form):
    """Optional product and region filters for dashboard data."""

    product = forms.ChoiceField(required=False, label="Product")
    region = forms.ChoiceField(required=False, label="Region")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        products = Sale.objects.order_by().values_list("product", flat=True).distinct().order_by("product")
        regions = Sale.objects.order_by().values_list("region", flat=True).distinct().order_by("region")
        self.fields["product"].choices = [("", "All products"), *((value, value) for value in products)]
        self.fields["region"].choices = [("", "All regions"), *((value, value) for value in regions)]
