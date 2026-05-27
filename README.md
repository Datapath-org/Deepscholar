# Deepscholar
Hello, we are Deepscholar
</br>
### Description
We provide people in academia with a way to stay up to date on advances in science without it being tedious; we aim to make it interactive and dynamic. Our app will show you a summary of current academic articles, and little by little we will get to know you so we can recommend what you are really interested in.
</br>
### Affiliations:
- Autonomous University of Mexico (UNAM)
- National School of Higher Studies (ENES)
  
### Methodology:

To develop the project, a process was carried out in which different requirements were established so that DataPath could be successfully developed.
</br>
- The NASA ADS API was integrated to collect scientific articles.
- In backend development, code was implemented for data extraction from the API, as well as recommendation algorithms, and Django was also used.
- Frontend development was carried out to make the page visually appealing and easy to use for the user.
- Testing and validation.
### Installation and Execution

1. Clone the repository:
   git clone https://github.com/Datapath-org/Deepscholar.git
2. Create and activate the virtual environment:
   python -m venv venv
   venv\Scripts\activate  (Windows)
3. Install dependencies:
   pip install -r requirements.txt
4. Set up environment variables:
   Create a .env file inside the Blog/ folder with:
   SECRET_KEY=your_secret_key
   API_TOKEN=your_nasa_ads_token
5. Run the server:
   cd Blog
   python manage.py runserver 
### Implementation
- Backend:  Python and Django
- Frontend: HTML, CSS, JavaScript  
### Testing
Manual testing was performed covering user registration, login, article browsing, saving and personalized recommendation loading.
### Results 

A functional web application was developed that consumes the NASA ADS API, displays scientific articles, and generates personalized recommendations based on the user's saved article history using cosine similarity between semantic vectors.
### Team members
Líder: Paola Castillo pcstillo6@gmail.com
</br>
Testing: Alejandro Cons Andablo alexmixsep@gmail.com
</br>
Tecnologías: Enrique Luviano kikeluviano1810@gmail.com
