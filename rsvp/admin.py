from django.contrib import admin

from .models import ExpectedGuest, Guest, Invite

admin.site.index_template = "rsvp/admin_index.html"


class ExpectedGuestInline(admin.TabularInline):
    model = ExpectedGuest
    extra = 0
    verbose_name = "Convidado esperado (uso interno)"
    verbose_name_plural = "Convidados esperados (uso interno)"


class GuestInline(admin.TabularInline):
    model = Guest
    extra = 0
    verbose_name = "Convidado confirmado (preenchido pelo convidado)"
    verbose_name_plural = "Convidados confirmados (preenchido pelo convidado)"


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ("number", "num_passes", "confirmed", "confirmed_at")
    list_filter = ("confirmed",)
    search_fields = ("number", "expected_guests__name", "guests__name")
    inlines = [ExpectedGuestInline, GuestInline]


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ("name", "invite", "slot")
    search_fields = ("name", "invite__number")


@admin.register(ExpectedGuest)
class ExpectedGuestAdmin(admin.ModelAdmin):
    list_display = ("name", "invite", "slot")
    search_fields = ("name", "invite__number")
