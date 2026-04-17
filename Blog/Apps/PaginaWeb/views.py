from django.shortcuts import render

import requests, json
from urllib.parse import urlencode, quote_plus

# Create your views here.
def home(request):

    token = "A6Utcox848aVp9tunWYvadPEc7fs41W51W5C4KUR"

    # Pagínador
    start = 0

    # Almacena articulos
    retrieved = []


    encoded_query = urlencode({
                               "q": "victor de la luz",
                               "fl": "author, title, citation_count", 
                               "start": start,
                               "rows": 10**10
                              })

    results = requests.get(f"https://api.adsabs.harvard.edu/v1/search/query?{encoded_query}", headers = {'Authorization': 'Bearer ' + token})

    data = results.json()

    docs = data["response"]["docs"]

    return render(request, "index.html", {
        'docs': docs
    })