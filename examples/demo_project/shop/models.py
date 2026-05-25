from django.db import models


class Customer(models.Model):
    """People who place orders."""

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "shop_customer"


class Product(models.Model):
    sku = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "shop_product"


class Order(models.Model):
    """Customer purchase header."""

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    status = models.CharField(max_length=32, default="pending")
    placed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "shop_order"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "shop_orderitem"
