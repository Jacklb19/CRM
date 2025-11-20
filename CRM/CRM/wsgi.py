"""
WSGI config for CRM project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application

# Asegura que Django use tu archivo de settings correcto
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CRM.settings')

# Render necesita esta aplicación WSGI para levantar el servidor con Gunicorn
application = get_wsgi_application()


#para commit
