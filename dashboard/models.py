"""Database models for the dashboard app."""

from django.db import models


class Sale(models.Model):
    date = models.DateField()
    product = models.CharField(max_length=100)
    region = models.CharField(max_length=50)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["date", "id"]

    def __str__(self):
        return f"{self.product} sale on {self.date}"
