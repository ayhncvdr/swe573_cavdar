# yourapp/context_processors.py

import os

def my_api_key(request):
    return {'myAPIKey': os.environ.get('GEOAPIFY_KEY')}
