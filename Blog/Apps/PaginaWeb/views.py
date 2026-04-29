from django.shortcuts import render

import requests, json
from urllib.parse import urlencode, quote_plus

from dotenv import load_dotenv
import os

load_dotenv()

# Create your views here.
def home(request):

    token = os.getenv('API_TOKEN')

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


from django.http import HttpResponse
from models import Flux
from datetime import datetime

def index(request):
    data=Flux.objects.values
    now = datetime.now()
    flux = Flux(now, 1.0)
    return HttpResponse("Este es mi microservicio")