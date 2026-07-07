from django.urls import path

from . import views

app_name = "rsvp"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/convite/buscar/", views.buscar_convite, name="buscar_convite"),
    path("api/convite/confirmar/", views.confirmar_presenca, name="confirmar_presenca"),
]
