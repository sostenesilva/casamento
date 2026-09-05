from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "rsvp"

urlpatterns = [
    path("", views.index, name="index"),
    path("api/convite/buscar/", views.buscar_convite, name="buscar_convite"),
    path("api/convite/confirmar/", views.confirmar_presenca, name="confirmar_presenca"),
    path("painel-confirmacoes/", views.painel_confirmacoes, name="painel_confirmacoes"),

    path("login/", auth_views.LoginView.as_view(template_name="rsvp/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("convites/", views.lista_convites, name="lista_convites"),
    path(
        "convites/<int:invite_id>/reconfirmar-whatsapp/",
        views.alternar_reconfirmado_whatsapp,
        name="alternar_reconfirmado_whatsapp",
    ),
]
