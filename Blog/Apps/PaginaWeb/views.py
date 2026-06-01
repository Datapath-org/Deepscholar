# Enrque
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
    def __init__(self, n_interests=6):
        self.n_interests = n_interests
        self.interests = []  # Lista de vectores centro (tensores)
        self.weights = []    # Importancia de cada interés
    
    def update_from_database(self, user):
        """Carga el perfil desde la base de datos"""
        try:
            # Obtener o crear perfil de usuario
            profile, created = models.UserProfile.objects.get_or_create(user=user)
            
            # Cargar intereses y pesos desde la BD
            if profile.interests and len(profile.interests) > 0:
                # Convertir listas guardadas a tensores
                self.interests = [torch.tensor(interest) for interest in profile.interests]
                self.weights = [torch.tensor(weight) for weight in profile.weights]
                return self.interests
            else:
                # Perfil vacío
                self.interests = []
                self.weights = []
                return None
                
        except Exception as e:
            print(f"Error cargando perfil: {e}")
            self.interests = []
            self.weights = []
            return None
    
    def save_to_database(self, user):
        """Guarda el perfil actual en la base de datos"""
        try:
            profile = models.UserProfile.objects.get(user=user)
            
            # Convertir tensores a listas para JSON
            profile.interests = [i.cpu().numpy().tolist() if torch.is_tensor(i) else i for i in self.interests]
            profile.weights = [w.cpu().item() if torch.is_tensor(w) else w for w in self.weights]
            profile.save()
            
            print(f"Perfil guardado: {len(self.interests)} intereses")
            
        except models.UserProfile.DoesNotExist:
            # Crear nuevo perfil
            models.UserProfile.objects.create(
                user=user,
                interests=[i.cpu().numpy().tolist() if torch.is_tensor(i) else i for i in self.interests],
                weights=[w.cpu().item() if torch.is_tensor(w) else w for w in self.weights]
            )
            print(f"Nuevo perfil creado: {len(self.interests)} intereses")
    
    def add_interaction(self, user, item_vector, weight=1.0):
        """Añade una interacción al perfil"""
        
        # Asegurar que item_vector es tensor
        if not torch.is_tensor(item_vector):
            item_vector = torch.tensor(item_vector)
        
        # Aplanar si es necesario (de (1,768) a (768))
        if item_vector.dim() > 1:
            item_vector = item_vector.squeeze()
        
        print(f"Añadiendo interacción. Vector shape: {item_vector.shape}")
        
        if len(self.interests) == 0:
            # Primer interés
            self.interests.append(item_vector)
            self.weights.append(torch.tensor(weight))
            self.save_to_database(user)
            print(f"Primer interés añadido!")
            
        else:
            # Encontrar interés más cercano usando cosine similarity
            similarities = []
            for interest in self.interests:
                # Normalizar vectores para cosine similarity
                cos_sim = torch.nn.functional.cosine_similarity(
                    item_vector.unsqueeze(0), 
                    interest.unsqueeze(0)
                )
                similarities.append(cos_sim.item())
            
            best_match_idx = np.argmax(similarities)
            best_similarity = similarities[best_match_idx]
            
            print(f"Mejor similitud: {best_similarity:.4f}")
            
            if best_similarity > 0.7:  # Umbral de similitud
                # Actualizar interés existente
                total_weight = self.weights[best_match_idx] + weight
                self.interests[best_match_idx] = (
                    self.interests[best_match_idx] * self.weights[best_match_idx] + 
                    item_vector * weight
                ) / total_weight
                self.weights[best_match_idx] = total_weight
                print(f"Interés actualizado (peso: {total_weight:.1f})")
                
            elif len(self.interests) < self.n_interests:
                # Nuevo interés
                self.interests.append(item_vector)
                self.weights.append(torch.tensor(weight))
                print(f"Nuevo interés añadido! Total: {len(self.interests)}/{self.n_interests}")
                
            else:
                # Reemplazar el menos importante
                min_weight_idx = torch.argmin(torch.tensor(self.weights)).item()
                self.interests[min_weight_idx] = item_vector
                self.weights[min_weight_idx] = torch.tensor(weight)
                print(f"Interés reemplazado (era peso {self.weights[min_weight_idx].item():.1f})")
            
            self.save_to_database(user)
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
    profile = MultiInterestUserProfile()

    saved_interest = profile.update_from_database(user)
    
    # Almacenar los documentos a mostrar
    r_docs = []
    

    # Formula cos(x) = |v1 * v2| / |v1| * |v2|
    if saved_interest:   # Todo el procesamiento de recomendación basado en similitud de dirección de vectores
        # Ver si ya hay intereses creados
        top_k=5 #Cuantos textos vamos a mostrar del total de los textos obtenidos?
        lista=[]
        for c in range(len(new_papers)):
            vector_consulta = encode(new_papers[c])
        
            # Calcular similitud con todos los textos del catálogo
            similitudes = []
            for i, vector_catalogo in enumerate(saved_interest):
                sim = torch.dot(vector_consulta.squeeze(), vector_catalogo)
                similitudes.append((i, sim))
            
            # Ordenar por similitud (mayor a menor)
            similitudes.sort(key=lambda x: x[1], reverse=True)
            
            # Devolver los top_k (excluyendo el mismo si coincide)
            resultados = []
            for idx, sim in similitudes[:top_k+1]:
                if sim < 0.999:  # Evitar el mismo texto si está en el catálogo
                    resultados.append((saved_interest[idx], sim))
            if resultados:

                lista.append((resultados[0][1],docs[c]))
            else: break
        r_docs = sorted(lista, key=lambda x: x[0])
    else:   # Simplemente aleatorizo los papers
        print("paper aleatorio")
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

    # Abstracts de los nuevos papers 
    new_papers = [doc.get('abstract', '') for doc in docs]
    
    # Vector de guardados del usuario
    user = request.user
    profile = MultiInterestUserProfile()

    saved_interest = profile.update_from_database(user)
    
    # Almacenar los documentos a mostrar
    r_docs = []

    

    # Formula cos(x) = |v1 * v2| / |v1| * |v2|
    if saved_interest:   # Todo el procesamiento de recomendación basado en similitud de dirección de vectores
        # Ver si ya hay intereses creados
        top_k=5 #Cuantos textos vamos a mostrar del total de los textos obtenidos?
        lista=[]
        for c in range(len(new_papers)):
            vector_consulta = encode(new_papers[c])
        
            # Calcular similitud con todos los textos del catálogo
            similitudes = []
            for i, vector_catalogo in enumerate(saved_interest):
                sim = torch.dot(vector_consulta.squeeze(), vector_catalogo)
                similitudes.append((i, sim))
            
            # Ordenar por similitud (mayor a menor)
            similitudes.sort(key=lambda x: x[1], reverse=True)
            
            # Devolver los top_k (excluyendo el mismo si coincide)
            resultados = []
            for idx, sim in similitudes[:top_k+1]:
                if sim < 0.999:  # Evitar el mismo texto si está en el catálogo
                    resultados.append((saved_interest[idx], sim))
            if resultados:

                lista.append((resultados[0][1],docs[c]))
            else: break
        r_docs = sorted(lista, key=lambda x: x[0])
    else:   # Simplemente aleatorizo los papers
        print("paper aleatorio")
        r_docs = docs
        random.shuffle(r_docs)
        
    # Para que aparezca el boton de borrar
    for r_doc in r_docs:
        r_doc["liked"] = models.Saved.objects.filter(
                                                    bibcode=r_doc['bibcode'],
                                                    user=user,
        ).exists()    

    return render(request, "index.html", {
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
def savePaper(request, bibcode):
    print(f"Guardando paper: {bibcode}")
    
    # Obtener datos del paper (tu código existente)
    encoded_query = urlencode({
        "start": 0,
        "rows": 1,
        "fl": "bibcode, title, author, abstract, pubdate, citation_count",
        "q": f"{bibcode}",
    })
    
    results = requests.get(
        f"https://api.adsabs.harvard.edu/v1/search/query?{encoded_query}",
        headers={'Authorization': 'Bearer ' + token}
    )
    
    data = results.json()
    docs = data["response"]["docs"][0]
    
    # Generar embedding
    abstract = docs.get('abstract', '')
    embedding = encode(abstract)  # Esto devuelve tensor (1, 768) o (768,)
    
    # Asegurar que embedding es 1D
    if embedding.dim() > 1:
        embedding = embedding.squeeze()
    
    print(f"Embedding shape: {embedding.shape}")
    
    # Guardar en Saved (tu código existente)
    paper = models.Saved.objects.create(
        bibcode=bibcode,
        title=docs.get('title', [''])[0],
        author=docs.get('author', ''),
        abstract=abstract,
        pubdate=docs.get('pubdate', ''),
        vect_text=embedding.cpu().numpy().tolist(),
        citation_count=docs.get('citation_count', 0),
        user=request.user
    )
    
    # ACTUALIZAR PERFIL DE INTERESES
    user = request.user
    profile = MultiInterestUserProfile()
    
    # Cargar perfil existente
    existing_interests = profile.update_from_database(user)
    print(f"Perfil cargado: {len(profile.interests)} intereses existentes")
    
    # Añadir nueva interacción
    profile.add_interaction(user, embedding, weight=1.0)
    
    return JsonResponse({"status": "ok"})

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
#Hola comentario
