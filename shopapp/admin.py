from django.contrib import admin
from .models import *

# Register your models here.

admin.site.register(UserDetails)
admin.site.register(Employee)
admin.site.register(Customer)
admin.site.register(Medicine)
admin.site.register(Dealer)
admin.site.register(Sale)
admin.site.register(Purchase)
admin.site.register(Delivery)
admin.site.register(Lead)
admin.site.register(Opportunity)
admin.site.register(OpportunityItems)
admin.site.register(SalesOrder)
admin.site.register(SalesOrderItems)
admin.site.register(LeadTablet)
admin.site.register(PurchaseItem)
admin.site.register(SaleItem)