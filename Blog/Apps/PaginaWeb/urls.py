from django.urls import path
from Apps.PaginaWeb.views import home

urlpatterns = [
    path('', home, name="index")
]