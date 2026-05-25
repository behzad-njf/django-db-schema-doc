from django.db import models


class Customer(models.Model):
    """People who place orders."""

    email = models.EmailField(
        "Email address",
        unique=True,
        help_text="Primary contact email for the customer.",
    )
    name = models.CharField("Full name", max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "shop_customer"


class Product(models.Model):
    """Catalog item available for purchase."""

    sku = models.CharField("SKU", max_length=64, unique=True)
    title = models.CharField("Title", max_length=255)
    price = models.DecimalField(
        "Unit price",
        max_digits=12,
        decimal_places=2,
        help_text="Price in the shop's default currency.",
    )

    class Meta:
        db_table = "shop_product"
        verbose_name = "product"
        verbose_name_plural = "products"


class Order(models.Model):
    """Customer purchase header."""

    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    status = models.CharField(
        "Order status",
        max_length=32,
        default="pending",
        help_text="e.g. pending, paid, shipped, cancelled.",
    )
    placed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "shop_order"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "shop_orderitem"
