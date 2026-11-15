"""Tests for the dashboard and sales CSV import."""

from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Sale


class DashboardPageTests(TestCase):
    def test_home_page_and_summary_calculations(self):
        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_revenue"], Decimal("313.95"))
        self.assertEqual(response.context["total_orders"], 6)
        self.assertEqual(response.context["total_quantity"], 50)
        self.assertEqual(response.context["best_selling_product"], "Notebook")
        self.assertEqual(response.context["best_selling_quantity"], 27)
        self.assertContains(response, "313.95")

    def test_empty_sales_table_has_zero_summaries(self):
        Sale.objects.all().delete()

        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_revenue"], 0)
        self.assertEqual(response.context["total_orders"], 0)
        self.assertEqual(response.context["total_quantity"], 0)
        self.assertEqual(response.context["best_selling_product"], "No sales yet")
        self.assertContains(response, "No sales records match the current selection.")

    def test_sql_practice_route_shows_all_four_examples(self):
        response = self.client.get(reverse("dashboard:sql_practice"))

        self.assertEqual(response.status_code, 200)
        examples = response.context["examples"]
        self.assertEqual(len(examples), 4)
        self.assertIn("WHERE", examples[0]["sql"])
        self.assertIn("ORDER BY", examples[1]["sql"])
        self.assertIn("GROUP BY", examples[2]["sql"])
        self.assertIn("SUM(quantity)", examples[3]["sql"])
        self.assertEqual(examples[3]["rows"], [(50, 6)])

    def test_chart_data_matches_sales_aggregates(self):
        response = self.client.get(reverse("dashboard:home"))

        self.assertEqual(response.status_code, 200)
        chart_data = response.context["chart_data"]
        self.assertEqual(chart_data["products"]["labels"], ["Desk Lamp", "Notebook", "Pen Set"])
        self.assertEqual(chart_data["products"]["values"], [5, 27, 18])
        self.assertEqual(chart_data["regions"]["labels"], ["East", "North", "South", "West"])
        self.assertEqual(chart_data["regions"]["values"], [14, 13, 15, 8])
        self.assertEqual(chart_data["daily_sales"]["values"], [12, 8, 3, 15, 2, 10])

    def test_product_filter_updates_summaries_table_and_charts(self):
        response = self.client.get(reverse("dashboard:home"), {"product": "Notebook"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_revenue"], Decimal("94.50"))
        self.assertEqual(response.context["total_orders"], 2)
        self.assertEqual(response.context["total_quantity"], 27)
        self.assertEqual(response.context["best_selling_product"], "Notebook")
        self.assertEqual(response.context["chart_data"]["products"]["labels"], ["Notebook"])
        self.assertEqual(response.context["chart_data"]["regions"]["values"], [12, 15])
        self.assertEqual(len(response.context["sales"]), 2)
        self.assertContains(response, "Notebook")
        self.assertTrue(all(sale.product == "Notebook" for sale in response.context["sales"]))

    def test_product_and_region_filters_can_be_combined(self):
        response = self.client.get(
            reverse("dashboard:home"), {"product": "Desk Lamp", "region": "East"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_revenue"], Decimal("49.98"))
        self.assertEqual(response.context["total_orders"], 1)
        self.assertEqual(response.context["total_quantity"], 2)
        self.assertEqual(len(response.context["sales"]), 1)

    def test_invalid_filter_value_shows_error_and_keeps_page_working(self):
        response = self.client.get(reverse("dashboard:home"), {"product": "Unknown product"})

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["filter_form"].errors)
        self.assertEqual(response.context["total_orders"], 6)

    def test_primary_routes_respond(self):
        for route in ("dashboard:home", "dashboard:sql_practice"):
            with self.subTest(route=route):
                self.assertEqual(self.client.get(reverse(route)).status_code, 200)

        self.assertEqual(self.client.get(reverse("dashboard:upload_sales")).status_code, 405)
        self.assertEqual(self.client.get("/not-a-page/").status_code, 404)


class SalesCSVUploadTests(TestCase):
    def upload_csv(self, contents, filename="sales.csv", follow=False):
        uploaded_file = SimpleUploadedFile(
            filename, contents.encode("utf-8"), content_type="text/csv"
        )
        return self.client.post(
            reverse("dashboard:upload_sales"), {"csv_file": uploaded_file}, follow=follow
        )

    def test_valid_csv_is_imported_and_shown_on_dashboard(self):
        response = self.upload_csv(
            "date,product,region,quantity,unit_price\n"
            "2026-02-01,Marker,East,4,2.75\n",
            follow=True,
        )

        self.assertEqual(response.redirect_chain, [(reverse("dashboard:home"), 302)])
        self.assertTrue(Sale.objects.filter(product="Marker", quantity=4).exists())
        self.assertContains(response, "Marker")
        self.assertContains(response, "Imported 1 sales records successfully.")

    def test_missing_required_column_is_rejected(self):
        response = self.upload_csv("date,product,region,quantity\n2026-02-01,Marker,East,4\n")

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Missing required column", status_code=400)
        self.assertEqual(Sale.objects.count(), 6)

    def test_non_csv_file_is_rejected(self):
        response = self.upload_csv(
            "date,product,region,quantity,unit_price\n2026-02-01,Marker,East,4,2.75\n",
            filename="sales.txt",
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, ".csv extension", status_code=400)
        self.assertEqual(Sale.objects.count(), 6)

    def test_invalid_quantity_is_rejected_without_importing_rows(self):
        response = self.upload_csv(
            "date,product,region,quantity,unit_price\n"
            "2026-02-01,Marker,East,many,2.75\n"
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "Row 2", status_code=400)
        self.assertEqual(Sale.objects.count(), 6)

    def test_invalid_date_and_price_are_rejected(self):
        invalid_rows = (
            "not-a-date,Marker,East,4,2.75",
            "2026-02-01,Marker,East,4,not-a-price",
        )
        for row in invalid_rows:
            with self.subTest(row=row):
                response = self.upload_csv(
                    "date,product,region,quantity,unit_price\n" + row + "\n"
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(Sale.objects.count(), 6)

    def test_existing_duplicate_record_is_rejected(self):
        response = self.upload_csv(
            "date,product,region,quantity,unit_price\n"
            "2026-01-05,Notebook,East,12,3.50\n"
        )

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "already in the database", status_code=400)
        self.assertEqual(Sale.objects.count(), 6)

    def test_duplicate_rows_in_one_file_are_rejected(self):
        row = "2026-02-01,Marker,East,4,2.75\n"
        response = self.upload_csv("date,product,region,quantity,unit_price\n" + row + row)

        self.assertEqual(response.status_code, 400)
        self.assertContains(response, "duplicates row 2", status_code=400)
        self.assertEqual(Sale.objects.count(), 6)

    def test_reuploading_the_same_csv_is_rejected(self):
        contents = "date,product,region,quantity,unit_price\n2026-02-01,Marker,East,4,2.75\n"

        first_response = self.upload_csv(contents)
        second_response = self.upload_csv(contents)

        self.assertEqual(first_response.status_code, 302)
        self.assertEqual(second_response.status_code, 400)
        self.assertContains(second_response, "already in the database", status_code=400)
        self.assertEqual(Sale.objects.filter(product="Marker").count(), 1)
