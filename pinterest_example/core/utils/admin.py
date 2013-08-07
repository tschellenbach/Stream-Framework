

import logging
from django.contrib.admin.sites import AlreadyRegistered
logger = logging.getLogger(__name__)


def auto_configure_admin(model):
    '''
    Automatic configuration, let's make this smarter
    in the future
    '''
    from django.contrib import admin
    from django.db import models
    fields = model._meta.fields
    field_names = [f.name for f in fields]
    list_display = [f for f in field_names if f not in (
        'updated_at', 'created_at')]
    fields_in_list_display = list_display[:7]
    list_editable_fields = [
        f.name for f in fields if isinstance(f, models.IntegerField)]
    search_fields_list = [f.name for f in fields if isinstance(
        f, (models.TextField, models.CharField))]

    class StandardAdmin(admin.ModelAdmin):
        list_display = fields_in_list_display
        list_editable = list_editable_fields
        search_fields = search_fields_list
    return StandardAdmin


def auto_register(models_module):
    from django.contrib import admin
    from django.db import models
    from django.core.exceptions import ImproperlyConfigured
    variables = dir(models_module)
    variables = filter(lambda x: not x.startswith('__'), variables)
    for x in variables:
        value = getattr(models_module, x)
        try:
            model_class = issubclass(value, models.Model)
        except TypeError, e:
            model_class = False
        if model_class:
            try:
                admin_config = auto_configure_admin(value)
                admin.site.register(value, admin_config)
            except Exception, e:
                logger.info('couldnt register %s to the admin', value)
