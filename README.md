# Deepscholar
Hello, we are Deepscholar
</br>
### Description
We provide people in academia with a way to stay up to date on advances in science without it being tedious; we aim to make it interactive and dynamic. Our app will show you a summary of current academic articles, and little by little we will get to know you so we can recommend what you are really interested in.
</br>
## Explaining the code
The code for the request of information by the API is really simple, the API we are using is from NASA ADS and they make everything easy to use.</br>

### In the views.py file

1. The first step is get the TOKEN from the ```.env``` hidden file for the API, we do that using the libraries: ```dotenv``` and ```os```. 

```token = os.getenv('API_TOKEN')```

2. And then we start with the retrieving of information. The ```start``` variable is used to indicate from which position we want to start reatrieving the results, and we start from the beginning, that is, position 0.

```
# Pagínador
start = 0
```

3. And now we are in the important part, this is the request. First, the query parameters are encoded using ```urlencode```. This is necessary so the API can correctly interpret the request, especially when the query contains spaces or special characters.

```
encoded_query = urlencode({
                           "q": "victor de la luz",
                           "fl": "author, title, citation_count",
                           "start": start,
                           "rows": 10**10    # This is, in practical terms, infinite, used to get all the articles
                          })
results = requests.get(f"https://api.adsabs.harvard.edu/v1/search/query?{encoded_query}", headers = {'Authorization': 'Bearer ' + token})
```

For the query we use 4 fields, for our project we include:
</br>
- ```q```: The query itself.
- ```fl```: This is the data we want to retrieve from the articles found.
- ```start```: As we say earlier, this is used to indicate the position to start.
- ```rows```: This parameter is used to indicate how many results we want to retrieve.

Once the query is encoded, it is appended to the URL. Then, a GET request is sent to the NASA ads API using the encoded query and the authorization token in the headers.

4. Finaly in the ```data``` variable we store the results and we apply json format for practical use. With the ```docs``` variable we get a dictionary with the data.

```
data = results.json()
docs = data["response"]["docs"]
```

3. Then, the data stored in the ```docs``` variable is sent to Django, which then uses it in an HTML template to display the results using a loop.

```
return render(request, "index.html", {
  'docs': docs
})
```

### In the html template

We display the information in the HTML using a loop and Django’s built-in template tags

```
<ul>
  {% for doc in docs %}
  <li>
    <p><strong>Titulo:</strong> {{ doc.title.0 }}</p>
    <p><strong>Autores:</strong> {{ doc.author|join:", " }}</p>
    <p><strong>Número de veces citado:</strong> {{ doc.citation_count }}</p>
    <hr>
  </li>
  {% endfor %}
</ul>
```

This is a built-in for loop from Django. Django provides different template commands, which are written using ```{% %}``` syntax, while variables and objects are referenced using ```{{ }}```.”

- ```{% for doc in docs %}```: We declare the for loop as follows, for each document (```doc```) in the documents (```docs```) variable.
</br></br>
In the next rows we are accesing to the interest parts of the json dictionary from the document retrieved:

- ```{{ doc.title.0 }}```: List its title.
- ```{{ doc.author|join:", " }}```: List the authors and separate them with commas.
- ```{{ doc.citation_count }}```: List its citation count.
- ```{{% endfor %}}```: Finaly, we end the loop.

And this is the way we show the retrieved articles using the NASA ADS API

---

### Team members
Líder: Paola Castillo pcstillo6@gmail.com
</br>
Testing: Alejandro Cons Andablo alexmixsep@gmail.com
</br>
Tecnologías: Enrique Luviano kikeluviano1810@gmail.com
