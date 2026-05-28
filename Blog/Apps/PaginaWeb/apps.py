from django.apps import AppConfig


# class PaginawebConfig(AppConfig):
#     name = 'PaginaWeb'

from transformers import AutoTokenizer
from adapters import AutoAdapterModel


class PaginawebConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Apps.PaginaWeb'
    verbose_name= "Pagina Web"
    
    def ready(self):
        import sys
        if "migrate" in sys.argv or "makemigrations" in sys.argv:
            return
        global tokenizer, model
        PaginawebConfig.tokenizer = AutoTokenizer.from_pretrained('allenai/specter2_base')
        PaginawebConfig.model = AutoAdapterModel.from_pretrained('allenai/specter2_base')
        PaginawebConfig.model.load_adapter("allenai/specter2", source="hf", load_as="specter2", set_active=True)
        PaginawebConfig.model.eval()
        print("allenai/specter2_base se ha cargado")