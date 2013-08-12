from core import models as pinterest_models
from core.utils.admin import auto_register

from django.contrib import admin


class ItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'image', 'source_url', 'message')
    list_editable = ('source_url', 'message')

admin.site.register(pinterest_models.Item, ItemAdmin)

auto_register(pinterest_models)
