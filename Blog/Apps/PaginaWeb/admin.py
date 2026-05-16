from django.contrib import admin
from django.contrib.auth.models import User
from .models import Saved

# Para quitar el registro por defecto del modelo User de auth.models
admin.site.unregister(User)

# Register your models here.
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id','first_name','last_name','username','email')
    search_fields = ('first_name','last_name','username','email')
    list_filter = ('id','first_name','last_name','username','email')
    list_per_page = 10


@admin.register(Saved)
class SavedAdmin(admin.ModelAdmin):
    list_display = ('bibcode',
                    'title',
                    'author',
                    'abstract',
                    'vect_text',
                    'date',
                    'citation_count',
                    'user')
