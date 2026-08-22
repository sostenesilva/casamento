from pathlib import Path

import openpyxl
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from rsvp.models import ExpectedGuest, Invite


class Command(BaseCommand):
    help = (
        "Importa convites e a lista interna de convidados esperados (ExpectedGuest) a "
        "partir de uma planilha .xlsx com as colunas 'Nome' e 'Número do convite' "
        "(nessa ordem, sem cabeçalho). Não mexe nos convidados confirmados pelo próprio "
        "convidado (Guest)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "arquivo",
            nargs="?",
            default="senhas.xlsx",
            help="Caminho do arquivo .xlsx (padrão: senhas.xlsx)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Mostra o que seria feito sem alterar o banco.",
        )

    def handle(self, *args, **options):
        path = Path(options["arquivo"])
        dry_run = options["dry_run"]

        if not path.exists():
            raise CommandError(f"Arquivo não encontrado: {path}")

        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb.active

        invites = {}
        for row in ws.iter_rows(values_only=True):
            name, number = (row + (None, None))[:2]
            if name is None or number is None:
                continue
            invites.setdefault(str(number), []).append(str(name).strip())

        if not invites:
            self.stdout.write(self.style.WARNING("Nenhum dado encontrado na planilha."))
            return

        created_invites = updated_invites = expected_guests_count = 0

        with transaction.atomic():
            for number, names in invites.items():
                invite, was_created = Invite.objects.get_or_create(
                    number=number,
                    defaults={"num_passes": len(names)},
                )
                if was_created:
                    created_invites += 1
                elif invite.num_passes != len(names):
                    invite.num_passes = len(names)
                    if not dry_run:
                        invite.save(update_fields=["num_passes"])
                    updated_invites += 1

                if not dry_run:
                    invite.expected_guests.all().delete()
                    for slot, name in enumerate(names, start=1):
                        ExpectedGuest.objects.create(invite=invite, slot=slot, name=name)
                expected_guests_count += len(names)

            if dry_run:
                transaction.set_rollback(True)

        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(self.style.SUCCESS(
            f"{prefix}Convites processados: {len(invites)} "
            f"(criados: {created_invites}, atualizados: {updated_invites}). "
            f"Convidados esperados (uso interno): {expected_guests_count}."
        ))
