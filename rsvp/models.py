from django.db import models


class Invite(models.Model):
    number = models.CharField("Número do convite", max_length=10, unique=True)
    num_passes = models.PositiveSmallIntegerField("Quantidade de senhas")
    confirmed = models.BooleanField("Confirmado", default=False)
    confirmed_at = models.DateTimeField("Confirmado em", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Convite {self.number} ({self.num_passes} senha(s))"


class Guest(models.Model):
    invite = models.ForeignKey(Invite, related_name="guests", on_delete=models.CASCADE)
    slot = models.PositiveSmallIntegerField("Posição da senha")
    name = models.CharField("Nome", max_length=150)

    class Meta:
        ordering = ["slot"]
        unique_together = ("invite", "slot")

    def __str__(self):
        return f"{self.name} (convite {self.invite.number})"


class ExpectedGuest(models.Model):
    """Uso interno: quem a organização pretendia convidar em cada senha do convite.

    Serve de referência para os administradores compararem com o nome que o
    próprio convidado preencheu (`Guest`) — não é exibido nem editável pelo
    convidado no site.
    """

    invite = models.ForeignKey(Invite, related_name="expected_guests", on_delete=models.CASCADE)
    slot = models.PositiveSmallIntegerField("Posição da senha")
    name = models.CharField("Nome esperado (uso interno)", max_length=150)

    class Meta:
        ordering = ["slot"]
        unique_together = ("invite", "slot")
        verbose_name = "Convidado esperado (uso interno)"
        verbose_name_plural = "Convidados esperados (uso interno)"

    def __str__(self):
        return f"{self.name} (convite {self.invite.number}, uso interno)"
