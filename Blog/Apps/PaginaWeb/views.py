from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse

import requests, json
from urllib.parse import urlencode, quote_plus

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from dotenv import load_dotenv
import random
import os

from Apps.PaginaWeb.forms import CreateUserForm
from Apps.PaginaWeb import models

load_dotenv()
token = os.getenv('API_TOKEN')
# model = SentenceTransformer("microsoft/harrier-oss-v1-270m")
model = SentenceTransformer("all-MiniLM-L6-v2")

# Letras y numeros para aleatorizar la query
ascii = [chr(i) for i in range(65, 91)]   # Letras min
ascii.extend([chr(i) for i in range(97, 123)])  # Letras may

# Para la paginación
start = 0
rows = 10

# Create your views here.
    if saved:   # Todo el procesamiento de recomendación basado en similitud de dirección de flechas
        # Obtener el último paper guardado 
        last_saved = papers.first().abstract
        
        saved_vect = model.encode(saved)    # TODO: Ya están vectorizados   
        last_saved_vect = model.encode(last_saved)  # TODO: Ya está vectorizado
        new_papers_vect = model.encode(new_papers)

        # Formando tendencia del historial del usuario
        history_tend = np.mean(saved_vect, axis=0)

        # Tendencia al último articulo guardado
        user_tend = (0.3 * history_tend) + (0.7 * last_saved_vect)  # TODO: revisar
        print(user_tend)

        # Generando similitud entre la tendencia del usuario y los nuevos papers
        simil = cosine_similarity([user_tend], new_papers_vect)[0]

        # Ordenando por papers similares
        r_docs = list(zip(simil, docs))
        r_docs.sort(key=lambda x:x[0], reverse=True)
        r_docs = [doc[1] for doc in r_docs]
    
    else:   # Simplemente aleatorizo los papers
        r_docs = docs
        #random.shuffle(r_docs)
 
    # Para que aparezca el boton de borrar
    for r_doc in r_docs:
        r_doc["liked"] = models.Saved.objects.filter(
                                                    bibcode=r_doc['bibcode'],
                                                    user=user,
        ).exists()    

    return render(request, "index.html", {
        'docs': r_docs
    })

@login_required(login_url='login')
def carga_mas(request): 
    # Para cargar más articulos despues al clickear cargar más
    
    # Para la cuestion de cargar más, me ayuda a sumar a rows para cargar más
    #articulos
    page = int(request.GET.get("page", 1))

    # Paginador que depende de page
    start = (page - 1) * rows
    char = random.choice(ascii)
    
    # Parametros de la query
    encoded_query = urlencode({
                               "start": start,
                               "rows": rows,
                               "fl": "bibcode, title, author, abstract, pubdate, citation_count", 
                               "q": f"{char}",
                               "fq": "year:[1980 TO *]",
                               "sort": "citation_count desc"
                              })

    # Ejecuta query
    results = requests.get(f"https://api.adsabs.harvard.edu/v1/search/query?{encoded_query}", headers = {'Authorization': 'Bearer ' + token})
    
    data = results.json()
    docs = data["response"]["docs"]
    
    # De nuevo esto porque si el usuario le dio like antes de
    # cargar más, aquí no lo tendría en cuenta
    
    # Abstracts de los nuevos papers 
    new_papers = [doc.get('abstract', '') for doc in docs]
    
    # Vector de guardados del usuario
    user = request.user
    papers = models.Saved.objects.filter(user=user).order_by("-date")
    saved = [paper.abstract for paper in papers]

    # Almacenar los documentos a mostrar
    r_docs = []

    # Formula cos(x) = |v1 * v2| / |v1| * |v2|
    if saved:   # Todo el procesamiento de recomendación basado en similitud de dirección de flechas
        # Obtener el último paper guardado 
        last_saved = papers.first().abstract
        
        saved_vect = model.encode(saved)
        last_saved_vect = model.encode(last_saved)
        new_papers_vect = model.encode(new_papers)
    
        # Formando tendencia del historial del usuario
        history_tend = np.mean(saved_vect, axis=0)

        # Tendencia al último articulo guardado
        user_tend = (0.3 * history_tend) + (0.7 * last_saved_vect)

        # Generando similitud entre la tendencia del usuario y los nuevos papers
        simil = cosine_similarity([user_tend], new_papers_vect)[0]

        # Ordenando por papers similares
        r_docs = list(zip(simil, docs))
        r_docs.sort(key=lambda x:x[0], reverse=True)
        r_docs = [doc[1] for doc in r_docs]
    
    else:   # Simplemente aleatorizo los papers
        r_docs = docs
        random.shuffle(r_docs)
        
    # Para que aparezca el boton de borrar
    for r_doc in r_docs:
        r_doc["liked"] = models.Saved.objects.filter(
                                                    bibcode=r_doc['bibcode'],
                                                    user=user,
        ).exists()    
     
    return JsonResponse({   #Com
        'docs': r_docs
    })

def registerPage(request):
    # Si el usuario tiene una sesion iniciada
    if request.user.is_authenticated:
        return redirect('index')

    # Si no, inicia registro
    else:
        form = CreateUserForm()

        # Recibo los datos
        if request.method == 'POST':
            username = None
            form = CreateUserForm(request.POST)
            
            # Verifico si son correctos
            if form.is_valid():
                form.save()

                username = request.POST.get('username')
                password = request.POST.get('password1')
                auth = authenticate(request,username=username, password=password)
                
                # Si sí, los almaceno y retorno al index
                if auth is not None:
                    login(request,auth)
                    return redirect('index')

        context = {'form':form}
        return render(request, "register.html", context)


def loginPage(request):
    if request.user.is_authenticated:
        return redirect('index')
    else:
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect('index')
            else:
                messages.error(request, 'Nombre de usuario o contraseña incorrectos')
            
        return render(request, "login.html", {})

@login_required(login_url='login')
def logoutUser(request):
    logout(request)
    return redirect('login')

@login_required(login_url='login')
def savePaper(request,bibcode):

    # Encontrar paper 
    encoded_query = urlencode({
                               "start": 0,
                               "rows": 1,
                               "fl": "bibcode, title, author, abstract, pubdate, citation_count", 
                               "q": f"{bibcode}",
                              })

    # Ejecuta query
    results = requests.get(f"https://api.adsabs.harvard.edu/v1/search/query?{encoded_query}", headers = {'Authorization': 'Bearer ' + token})

    data = results.json()
    docs = data["response"]["docs"][0]

    bibcode = docs.get('bibcode', '')                   #docs['bibcode']
    #
    title = docs.get('title', [''])[0]                  #docs['title'][0]
    #
    author = docs.get('author','')                      #docs['author']
    #
    # try: abstract = docs['abstract']
    # except: abstract = ""
    abstract = docs.get('abstract','')                  #docs['abstract']
    #
    pubdate = docs.get('pubdate','')                    #docs['pubdate']
    #
    embedding = model.encode(abstract)
    vect_text = embedding.tolist()
    #
    citation_count = docs.get('citation_count','')      #docs['citation_count']

        
    paper = models.Saved.objects.create(
        bibcode=bibcode,
        title=title,
        author=author,
        abstract=abstract,
        pubdate=pubdate,
        vect_text=vect_text,
        citation_count=docs['citation_count'],
        user=request.user
    )

    return JsonResponse({
        "status":"ok"
    })

@login_required(login_url='login')
def deletePaper(request,bibcode):
    paper = models.Saved.objects.get(bibcode=bibcode)
    paper.delete()

    return JsonResponse({
        "status":"ok"
    })

@login_required(login_url='login')
def saved(request):
    user = request.user

    docs = models.Saved.objects.filter(user=user).order_by("-date")

    return render(request, "guardados.html", {
        "docs": docs
    })