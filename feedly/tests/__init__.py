
try:
    from django.conf import settings
    try:
        # ignore this if we already configured settings
        settings.configure()
    except RuntimeError as e:
        pass
except:
    pass
