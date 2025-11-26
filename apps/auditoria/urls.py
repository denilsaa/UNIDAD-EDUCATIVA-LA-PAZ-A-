from django.urls import path
from .views import historial_estudiantes

app_name = "auditoria"

urlpatterns = [
  path("estudiantes/", historial_estudiantes, name="historial_estudiantes"),
]
