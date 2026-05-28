from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse

from transformers import AutoTokenizer
from adapters import AutoAdapterModel

import requests, json
from urllib.parse import urlencode, quote_plus

from sentence_transformers import SentenceTransformer
#from sklearn.metrics.pairwise import cosine_similarity now we are using our own cosine similarity func
import numpy as np
from dotenv import load_dotenv
import random
import os
import torch
from .apps import PaginawebConfig
from Apps.PaginaWeb.forms import CreateUserForm
from Apps.PaginaWeb import models

load_dotenv()
token = 'A6Utcox848aVp9tunWYvadPEc7fs41W51W5C4KUR'
# model = SentenceTransformer("microsoft/harrier-oss-v1-270m")
# model = SentenceTransformer("all-MiniLM-L6-v2") commented cuz its too small for the task (180 word cap)
# Cargar modelo y tokenizador
#tokenizer = AutoTokenizer.from_pretrained('allenai/specter2_base')
#model = AutoAdapterModel.from_pretrained('allenai/specter2_base')
#model.load_adapter("allenai/specter2", source="hf", load_as="specter2", set_active=True) MOVED TO APPS.PY 



# Intentar importar las variables globales
try:
    from Blog.Apps.PaginaWeb import tokenizer, model
except ImportError:
    # Si no existen, cargarlas manualmente
    from transformers import AutoTokenizer
    from adapters import AutoAdapterModel
    tokenizer = AutoTokenizer.from_pretrained('allenai/specter2_base')
    model = AutoAdapterModel.from_pretrained('allenai/specter2_base')
    model.load_adapter("allenai/specter2", source="hf", load_as="specter2", set_active=True)
    model.eval()

class MultiInterestUserProfile:
    def __init__(self, n_interests=5):
        self.n_interests = n_interests
        self.interests = []  # Lista de vectores centro
        self.weights = []    # Importancia de cada interés
        
    def add_interaction(self, item_vector, weight=1.0):
        """Añade un nuevo gusto al perfil"""
        if len(self.interests) == 0:
            # Primer interés
            self.interests.append(item_vector)
            self.weights.append(weight)
        else:
            # Encontrar interés más cercano
            similarities = [np.dot(item_vector, interest) 
                          for interest in self.interests]
            best_match_idx = np.argmax(similarities)
            
            if similarities[best_match_idx] > 0.7:  # Umbral de similitud
                # Pertenece a interés existente → actualizar centro
                self.interests[best_match_idx] = (
                    self.interests[best_match_idx] * self.weights[best_match_idx] + 
                    item_vector * weight
                ) / (self.weights[best_match_idx] + weight)
                self.weights[best_match_idx] += weight
            elif len(self.interests) < self.n_interests:
                # Nuevo interés
                self.interests.append(item_vector)
                self.weights.append(weight)
            else:
                # Reemplazar el menos importante
                min_weight_idx = np.argmin(self.weights)
                self.interests[min_weight_idx] = item_vector
                self.weights[min_weight_idx] = weight

# Letras y numeros para aleatorizar la query
ascii = [chr(i) for i in range(65, 91)]   # Letras min
ascii.extend([chr(i) for i in range(97, 123)])  # Letras may

# Para la paginación
start = 0
rows = 10

#Nuevas funciones para el embedding del modelo

def encode(texts):
    
    if isinstance(texts, str):
        texts = [texts]
    model = PaginawebConfig.model
    inputs = PaginawebConfig.tokenizer(
        texts,
        return_tensors="pt", 
        truncation=True, 
        padding=True,      
        max_length=512
    )
    
    with torch.no_grad():  
        outputs = model(**inputs)
    
    embeddings_tokens = outputs.last_hidden_state
    embedding_paper = torch.mean(embeddings_tokens, axis=1)
    return embedding_paper

def cosine_similarity(emb1, emb2):
    return torch.nn.functional.cosine_similarity(emb1, emb2, dim=-1)



# Create your views here.
@login_required(login_url='login')
def home(request):
    
    # Para aleatorizar la query
    char = random.choice(ascii)

    # Parametros de la query
    encoded_query = urlencode({
                            "start": random.randint(0, 1000),
                            "rows": rows,
                            "fl": "bibcode, title, author, abstract, pubdate, citation_count", 
                            "q": f"{char}",
                            "fq": "year:[1950 TO *]",
                            "sort": "citation_count desc"
                            })

    # Ejecuta query
    results = requests.get(f"https://api.adsabs.harvard.edu/v1/search/query?{encoded_query}", headers = {'Authorization': 'Bearer ' + token})
    
    data = results.json()
    docs = data["response"]["docs"]

    # Abstracts de los nuevos papers 
    new_papers = [doc.get('abstract', '') for doc in docs]
    
    # Vector de guardados del usuario
    user = request.user
    papers = models.Saved.objects.filter(user=user).order_by("-date")
    saved = [paper.abstract for paper in papers]

    # Almacenar los documentos a mostrar
    r_docs = []
    

    # Formula cos(x) = |v1 * v2| / |v1| * |v2|
    if saved:   # Todo el procesamiento de recomendación basado en similitud de dirección de vectores
        # Obtener el último paper guardado 
        last_saved = papers.first().abstract
        
        saved_vect = encode(saved)
        
        last_saved_vect = encode(last_saved)
        new_papers_vect = encode(new_papers)
    
        # Formando tendencia del historial del usuario
        history_tend = torch.mean(saved_vect, axis=0)

        # Tendencia al último articulo guardado
        user_tend = (0.3 * history_tend) + (0.7 * last_saved_vect)

        # Generando similitud entre la tendencia del usuario y los nuevos papers
        simil = cosine_similarity(user_tend, new_papers_vect)

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

    return render(request, "index.html", {
        'docs': docs
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
    papers = models.UserProfile.objects.filter(user=user)
    saved = [paper.insterests for paper in papers]

    # Almacenar los documentos a mostrar
    r_docs = []

    
    def recommend(self, catalog_vectors, catalog_items, k=20):
        """Recomienda combinando múltiples intereses"""
        all_scores = np.zeros(len(catalog_vectors))
        
        # Cada interés contribuye proporcionalmente a su peso
        for interest, weight in zip(self.interests, self.weights):
            scores = np.dot(catalog_vectors, interest)
            all_scores += scores * weight
        
        # Normalizar
        all_scores = all_scores / sum(self.weights)
        
        # Top-k
        top_idx = np.argsort(all_scores)[-k:][::-1]
        return [(catalog_items[i], all_scores[i]) for i in top_idx]

# Recomendará principalmente programación (peso 2), algo de cocina (peso 1)
    # Formula cos(x) = |v1 * v2| / |v1| * |v2|
    if saved:   # Todo el procesamiento de recomendación basado en similitud de dirección de vecotres
        # Obtener el último paper guardado 
        last_saved = papers.first().abstract
        
        saved_vect = encode(saved)
        last_saved_vect = encode(last_saved)
        new_papers_vect = encode(new_papers)
    
        # Formando tendencia del historial del usuario
        history_tend = torch.mean(saved_vect, axis=0)

        # Tendencia al último articulo guardado
        user_tend = (0.3 * history_tend) + (0.7 * last_saved_vect)

        # Generando similitud entre la tendencia del usuario y los nuevos papers
        simil = cosine_similarity(user_tend, new_papers_vect)

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
                
    return JsonResponse({
        
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
    embedding = encode(abstract)
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