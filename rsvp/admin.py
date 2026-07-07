from django.contrib import admin

from .models import Guest, Invite


class GuestInline(admin.TabularInline):
    model = Guest
    extra = 0


@admin.register(Invite)
class InviteAdmin(admin.ModelAdmin):
    list_display = ("number", "num_passes", "confirmed", "confirmed_at")
    list_filter = ("confirmed",)
    search_fields = ("number",)
    inlines = [GuestInline]


@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ("name", "invite", "slot")
    search_fields = ("name", "invite__number")
