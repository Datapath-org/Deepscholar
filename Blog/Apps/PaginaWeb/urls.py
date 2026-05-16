from django.urls import path
from Apps.PaginaWeb import views

urlpatterns = [
    path('', views.home, name="index"),
    path('more/', views.carga_mas, name="more"),

    path('login/', views.loginPage, name='login'),
    path('register/', views.registerPage, name='register'),
    path('logout/', views.logoutUser, name='logout'),
    path('save/<str:bibcode>/', views.savePaper, name='save'),
    path('delete/<str:bibcode>/', views.deletePaper, name='delete'),
    path('saved/', views.saved, name='saved')
]