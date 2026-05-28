from django.db import models
from django.contrib.auth.models import User

# Create your models here.
# class User(models.Model):
#     gndr = (
#         ("M", "Másculino"),
#         ("F", "Femenino"),
#         ("O", "Otro"),
#     )

#     uid = models.BigAutoField(primary_key=True, editable=False, verbose_name="Id")
#     ufname = models.CharField(max_length=255, verbose_name="Nombre/s")
#     ulname = models.CharField(max_length=255, verbose_name="Apellidos")
#     username = models.CharField(unique=True, max_length=20, verbose_name="Sobrenombre")
#     ugndr = models.CharField(max_length=1, blank=True, choices=gndr, verbose_name="Género")
#     uemail = models.EmailField(default="Sin Email", verbose_name="Email")


#     class Meta:
#         verbose_name = 'Usuario'
#         verbose_name_plural = 'Usuarios'
#         db_table = 'USER'
    
#     def __str__(self):
#         return "{} {}".format(self.ufname, self.ulname)

class Saved(models.Model):
    bibcode = models.CharField(max_length=19,primary_key=True,verbose_name="Bibcode")
    title = models.TextField(verbose_name="Titulo")
    author = models.JSONField(verbose_name="Autor/es")
    abstract = models.TextField(verbose_name="Resumen")
    pubdate = models.CharField(max_length=10,verbose_name="Fecha de Publicación")
    vect_text = models.JSONField(verbose_name="Texto Vectorizado")
    citation_count = models.IntegerField(verbose_name="No. de Citas")
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Like")

    class Meta:
        verbose_name = 'Guardado'
        verbose_name_plural = 'Guardados'
        db_table = 'GUARDADO'


