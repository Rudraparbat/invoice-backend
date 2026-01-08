from django.contrib import admin
from .models import Branches, InvoiceUser , InvoiceData
# Register your models here.
admin.site.register(InvoiceUser)
admin.site.register(InvoiceData)
admin.site.register(Branches)