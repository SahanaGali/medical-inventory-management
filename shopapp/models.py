# models.py
from django.db import models
from django.contrib.auth.models import User
from .validators import validate_phone_number
import datetime
from decimal import Decimal
from django.db.models import Sum
from django.db import models
from decimal import Decimal
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.db import transaction

class UserDetails(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, verbose_name="User Role")

    def __str__(self):
        return self.user.username

class Employee(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    emp_id = models.CharField(max_length=10)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    phone_number = models.BigIntegerField()
    salary = models.BigIntegerField()
    mail_id = models.EmailField()
    profile_picture = models.ImageField(upload_to='profile', blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=50,blank=True,null=True)
    password = models.CharField(max_length=20, null=True, blank=True)
    address = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    pincode = models.IntegerField(null=True, blank=True)
    phone_number = models.BigIntegerField()
    mail_id = models.EmailField(null=True, blank=True)
    role = models.CharField(max_length=20, null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile', blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Dealer(models.Model):
    dealer_name = models.CharField(max_length=100)
    company_name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    phone = models.BigIntegerField()
    mail_id = models.EmailField()

    def __str__(self):
        return self.dealer_name

class Medicine(models.Model):
    medicine_name = models.CharField(max_length=100)
    medicine_code = models.CharField(max_length=20, blank=True, null=True)
    dealer_name = models.ForeignKey(Dealer, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    description = models.CharField(max_length=100, blank=True, null=True)
    total = models.PositiveIntegerField()

    def __str__(self):
        return str(self.medicine_name)
    
    def save(self, *args, **kwargs):
        self.total = self.price * self.stock
        super(Medicine, self).save(*args, **kwargs)

class Purchase(models.Model):
    dealer = models.ForeignKey(Dealer, on_delete=models.CASCADE)
    phone = models.BigIntegerField(verbose_name="Phone Number")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="Total Amount")
    status = models.BooleanField(default=False)

    def calculate_total_amount(self):
        total = sum(item.total for item in self.items.all())
        return total

    def save(self, *args, **kwargs):
        super(Purchase, self).save(*args, **kwargs)
        self.total_amount = self.calculate_total_amount()
        super(Purchase, self).save(update_fields=['total_amount'])

    def __str__(self):
        return f"Purchase from {self.dealer}"

class PurchaseItem(models.Model):
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='items')
    tablet_name = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.price is not None and self.quantity is not None:
            self.total = self.price * self.quantity  
        super().save(*args, **kwargs)  
        self.purchase.save()  

    def __str__(self):
        return f"{self.tablet_name} (Quantity: {self.quantity})"


def get_order_number():
    ord_num = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    order_number = ord_num
    return order_number

SALE_STATUS_CHOICES = [
    ('SALE COUNTER', 'SALE COUNTER'),
    ('SALE DELIVERY', 'SALE DELIVERY'),
]

class Sale(models.Model):
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    phone = models.BigIntegerField()
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    confirmed = models.CharField(max_length=20, choices=SALE_STATUS_CHOICES, blank=True, null=True)
    status = models.BooleanField(default=False)

    def calculate_total(self):
        subtotal = sum(item.sub_total for item in self.items.all())
        tax_amount = subtotal * (self.tax / Decimal('100'))
        return subtotal + tax_amount

    def save(self, *args, **kwargs):
        if self.pk:
            self.total = self.calculate_total()

            if self.confirmed == 'SALE DELIVERY' and self.status and not self.delivery_set.exists():
                delivery = Delivery.objects.create(
                    sale=self,
                    order_number=get_order_number() + str(self.pk),
                    status='PENDING'
                )
                for item in self.items.all():
                    delivery.sale_items.add(item)
            
            if self.confirmed == 'SALE COUNTER':
                processed_items = set()

                with transaction.atomic():
                    for item in self.items.all():
                        if item not in processed_items:
                            item.update_stock()
                            processed_items.add(item)

        super(Sale, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.customer.first_name} - {self.id}"

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.pk:  # Only calculate sub_total if creating a new SaleItem
            total_before_discount = self.price * self.quantity
            total_discount = total_before_discount * (self.discount / Decimal('100'))
            self.sub_total = total_before_discount - total_discount
        
        super().save(*args, **kwargs)

    def update_stock(self):
        self.medicine.stock -= self.quantity
        self.medicine.save()

    def __str__(self):
        return f"{self.medicine.medicine_name} (x{self.quantity})"


class Delivery(models.Model):
    order_number = models.CharField(max_length=20)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE)
    sale_items = models.ManyToManyField(SaleItem)
    status = models.CharField(max_length=30, default='PENDING')

    def __str__(self):
        return f"Delivery for Sale: {self.sale}"


class Lead(models.Model):
    name = models.ForeignKey(Customer,on_delete=models.CASCADE)
    phone = models.BigIntegerField()
    email = models.EmailField(blank=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name.user}"


class LeadTablet(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    tablet = models.ForeignKey(Medicine,on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(blank=True)

    def __str__(self):
        return f"{self.tablet.medicine_name} ({self.quantity})"

class Opportunity(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE)
    phone_number = models.BigIntegerField()
    email = models.EmailField(blank=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.lead.name.user}"

class OpportunityItems(models.Model):
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    tablet_name = models.ForeignKey(Medicine,on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.tablet_name.medicine_name} ({self.quantity})"

class SalesOrder(models.Model):
    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE)
    phone_number = models.BigIntegerField()
    email = models.EmailField(blank=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.opportunity.lead.name.user}"
    
class SalesOrderItems(models.Model):
    saleorder = models.ForeignKey(SalesOrder,on_delete=models.CASCADE)
    tablet_name = models.ForeignKey(Medicine,on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.tablet_name.medicine_name} ({self.quantity})"

