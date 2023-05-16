from django.forms import ModelForm
from .models import*

class StoryForm(ModelForm):
    class Meta:
        model = Story 
        fields = ['content']