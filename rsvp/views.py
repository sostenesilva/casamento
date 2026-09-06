import json

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from .models import ExpectedGuest, Guest, Invite


@require_GET
def index(request):
    return render(request, "rsvp/index.html")


@staff_member_required
def painel_confirmacoes(request):
    invites = Invite.objects.prefetch_related("expected_guests", "guests")

    rows = []
    confirmed_invites = 0
    total_confirmed_guests = 0

    for invite in invites:
        expected = list(invite.expected_guests.all())
        confirmed = list(invite.guests.all())
        confirmed_names = {g.name.strip().lower() for g in confirmed}
        expected_names = {g.name.strip().lower() for g in expected}

        for g in expected:
            g.was_confirmed = g.name.strip().lower() in confirmed_names
        for g in confirmed:
            g.matches_expected = g.name.strip().lower() in expected_names

        if invite.confirmed:
            confirmed_invites += 1
        total_confirmed_guests += len(confirmed)

        rows.append({"invite": invite, "expected": expected, "confirmed": confirmed})

    context = {
        **admin.site.each_context(request),
        "title": "Painel de confirmações",
        "rows": rows,
        "total_invites": invites.count(),
        "confirmed_invites": confirmed_invites,
        "pending_invites": invites.count() - confirmed_invites,
        "total_expected_guests": ExpectedGuest.objects.count(),
        "total_confirmed_guests": total_confirmed_guests,
    }
    return render(request, "rsvp/painel_confirmacoes.html", context)


@login_required
def lista_convites(request):
    invites = Invite.objects.prefetch_related("expected_guests", "guests")

    rows = []
    for invite in invites:
        expected = list(invite.expected_guests.all())
        confirmed = list(invite.guests.all())
        rows.append({
            "invite": invite,
            "expected": expected,
            "confirmed": confirmed,
        })

    return render(request, "rsvp/lista_convites.html", {
        "rows": rows,
        "tipo_choices": Invite.TIPO_CHOICES,
    })


@login_required
@require_POST
def alternar_reconfirmado_whatsapp(request, invite_id):
    invite = get_object_or_404(Invite, pk=invite_id)
    invite.reconfirmed_by_whatsapp = not invite.reconfirmed_by_whatsapp
    invite.save(update_fields=["reconfirmed_by_whatsapp", "updated_at"])
    return JsonResponse({"ok": True, "reconfirmed_by_whatsapp": invite.reconfirmed_by_whatsapp})


@login_required
@require_POST
def atualizar_contato_whatsapp(request, invite_id):
    invite = get_object_or_404(Invite, pk=invite_id)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Requisição inválida."}, status=400)

    whatsapp = str(data.get("whatsapp", "")).strip()
    if len(whatsapp) > 20:
        return JsonResponse({"ok": False, "error": "Número muito longo (máx. 20 caracteres)."}, status=400)

    invite.whatsapp = whatsapp
    invite.save(update_fields=["whatsapp", "updated_at"])
    return JsonResponse({"ok": True, "whatsapp": invite.whatsapp})


@login_required
@require_POST
def atualizar_tipo_convite(request, invite_id):
    invite = get_object_or_404(Invite, pk=invite_id)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Requisição inválida."}, status=400)

    invite_type = str(data.get("invite_type", "")).strip()
    valid_types = dict(Invite.TIPO_CHOICES)
    if invite_type not in valid_types:
        return JsonResponse({"ok": False, "error": "Tipo de convite inválido."}, status=400)

    invite.invite_type = invite_type
    invite.save(update_fields=["invite_type", "updated_at"])
    return JsonResponse({
        "ok": True,
        "invite_type": invite.invite_type,
        "invite_type_label": valid_types[invite.invite_type],
    })


@login_required
@require_POST
def alternar_entregue(request, invite_id):
    invite = get_object_or_404(Invite, pk=invite_id)
    invite.delivered = not invite.delivered
    invite.save(update_fields=["delivered", "updated_at"])
    return JsonResponse({"ok": True, "delivered": invite.delivered})


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
