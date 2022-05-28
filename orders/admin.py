from django.contrib import admin
from .models import Order, Payment, OrderProduct

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    readonly_fields = ('payment', 'user', 'product', 'quantity', 'product_price', 'ordered')
    extra = 0

class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'fullName', 'email', 'mobile', 'city', 'order_total', 'status', 'is_ordered', 'created_time']
    list_filter = ['status', 'is_ordered']
    search_fields = ['order_number', 'mobile', 'email', 'first_name', 'last_name']
    list_per_page = 20
    inlines = [OrderProductInline]

    


admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(OrderProduct)
