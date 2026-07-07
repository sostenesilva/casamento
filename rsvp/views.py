import json

from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import Guest, Invite


@require_GET
def index(request):
    return render(request, "rsvp/index.html")


def _find_invite(number):
    try:
        return Invite.objects.get(number__iexact=number)
    except Invite.DoesNotExist:
        pass

    if number.isdigit():
        target = int(number)
        for invite in Invite.objects.all():
            if invite.number.isdigit() and int(invite.number) == target:
                return invite

    return None


def _invite_payload(invite):
    names = ["" for _ in range(invite.num_passes)]
    for guest in invite.guests.all():
        if 1 <= guest.slot <= invite.num_passes:
            names[guest.slot - 1] = guest.name
    return {
        "number": invite.number,
        "num_passes": invite.num_passes,
        "confirmed": invite.confirmed,
        "confirmed_at": invite.confirmed_at.strftime("%d/%m/%Y às %H:%M") if invite.confirmed_at else None,
        "names": names,
    }


@require_POST
def buscar_convite(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Requisição inválida."}, status=400)

    number = str(data.get("number", "")).strip()
    if not number:
        return JsonResponse({"ok": False, "error": "Informe o número do convite."}, status=400)

    invite = _find_invite(number)
    if invite is None:
        return JsonResponse({"ok": False, "error": "Convite não encontrado. Confira o número e tente novamente."}, status=404)

    return JsonResponse({"ok": True, "invite": _invite_payload(invite)})


@require_POST
def confirmar_presenca(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Requisição inválida."}, status=400)

    number = str(data.get("number", "")).strip()
    names = data.get("names", [])

    invite = _find_invite(number)
    if invite is None:
        return JsonResponse({"ok": False, "error": "Convite não encontrado."}, status=404)

    if not isinstance(names, list) or len(names) != invite.num_passes:
        return JsonResponse(
            {"ok": False, "error": f"Este convite tem {invite.num_passes} senha(s)."},
            status=400,
        )

    cleaned = [str(name).strip() for name in names]
    if not any(cleaned):
        return JsonResponse({"ok": False, "error": "Preencha o nome de ao menos um convidado."}, status=400)

    for slot, name in enumerate(cleaned, start=1):
        if name:
            Guest.objects.update_or_create(invite=invite, slot=slot, defaults={"name": name})
        else:
            Guest.objects.filter(invite=invite, slot=slot).delete()

    invite.confirmed = True
    invite.confirmed_at = timezone.now()
    invite.save(update_fields=["confirmed", "confirmed_at", "updated_at"])

    return JsonResponse({"ok": True, "invite": _invite_payload(invite)})
