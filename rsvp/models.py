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
