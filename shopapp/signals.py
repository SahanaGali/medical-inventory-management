from django.db.models.signals import post_save,pre_save
from django.dispatch import receiver
from .models import *
from django.db import transaction


@receiver(post_save, sender=Delivery)
def update_stock(sender, instance, **kwargs):
    if instance.status == 'DELIVERED':
        for item in instance.sale.items.all():
            medicine = item.medicine
            if medicine.stock >= item.quantity:
                medicine.stock -= item.quantity
                medicine.save()
            else:
                print(f"Insufficient stock for {medicine.medicine_name}. Current stock: {medicine.stock}, required: {item.quantity}")



@receiver(post_save, sender=Purchase)
def update_stock_from_purchase(sender, instance, created, **kwargs):
    if instance.status and instance._previous_status != instance.status:
        print(instance.items.all().count())
        for item in instance.items.all():
            tablet = item.tablet_name
            # print(tablet)
            # print(item.quantity)
            tablet.stock += item.quantity
            tablet.save()

def update_purchase_previous_status(sender, instance, **kwargs):
    if instance.pk:
        instance._previous_status = Purchase.objects.get(pk=instance.pk).status
    else:
        instance._previous_status = None

models.signals.pre_save.connect(update_purchase_previous_status, sender=Purchase)

@receiver(post_save, sender=Lead)
def create_opportunity(sender, instance, created, **kwargs):
    if instance.status:
        opportunity = Opportunity.objects.create(
            lead=instance,
            # customer_name=instance.name.user,
            phone_number=instance.phone,
            email=instance.email,
            status=False,
        )

        lead_tablets = LeadTablet.objects.filter(lead=instance)
        for lead_tablet in lead_tablets:
            OpportunityItems.objects.create(
                opportunity=opportunity,
                tablet_name=lead_tablet.tablet,
                quantity=lead_tablet.quantity
            )

@receiver(post_save, sender=Opportunity)
def create_sales_order(sender, instance, created, **kwargs):
    if instance.status and not created:
        sales_order = SalesOrder.objects.create(
            opportunity=instance,
            phone_number=instance.phone_number,
            email=instance.email,
            status=False
        )

        opportunity_items = OpportunityItems.objects.filter(opportunity=instance)
        for opportunity_item in opportunity_items:
            SalesOrderItems.objects.create(
                saleorder=sales_order,
                tablet_name=opportunity_item.tablet_name,
                quantity=opportunity_item.quantity
            )


@receiver(post_save, sender=SalesOrder)
def create_sale(sender, instance, created, **kwargs):
    if instance.status and not created:  
        sale = Sale.objects.create(
            customer=instance.opportunity.lead.name,
            phone=instance.phone_number,
            tax=Decimal('0'),
            confirmed='SALE DELIVERY',
            status=False
        )

        sales_order_items = SalesOrderItems.objects.filter(saleorder=instance)
        for sales_order_item in sales_order_items:
            SaleItem.objects.create(
                sale=sale,
                medicine=sales_order_item.tablet_name,
                price=sales_order_item.tablet_name.price,  # Assuming Medicine model has a price field
                quantity=sales_order_item.quantity,
                discount=Decimal('5'),
                sub_total=sales_order_item.tablet_name.price * sales_order_item.quantity  # Assuming no discount
            )
        
        sale.total = sale.calculate_total()
        sale.save()