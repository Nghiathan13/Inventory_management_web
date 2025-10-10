from django.contrib import admin
from .models import Product, Order
from django.contrib.auth.models import Group


admin.site.site_header = 'Inventory Management Admin'

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'quantity')
    list_filter = ('category',)

class OrdertAdmin(admin.ModelAdmin):
    list_display = ('product', 'staff', 'date')
    list_filter = ('date',)


# Register your models here.
admin.site.register(Product , ProductAdmin)
admin.site.register(Order, OrdertAdmin)
# admin.site.unregister(Group)