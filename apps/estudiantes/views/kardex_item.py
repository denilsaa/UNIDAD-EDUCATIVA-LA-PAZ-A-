# apps/estudiantes/views/kardex_item.py
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from django.urls import reverse_lazy

from apps.estudiantes.models.kardex_item import KardexItem
from apps.estudiantes.forms import KardexItemForm

# 🔒 mixin por rol
from apps.cuentas.mixins import RoleRequiredMixin


class KardexItemListView(RoleRequiredMixin, ListView):
    model = KardexItem
    template_name = "kardex/items_lista.html"
    context_object_name = "items"
    paginate_by = 20
    required_roles = ("director", "secretaria", "secretaría")  # ⬅️ solo Dir/Secretaría

    def get_paginate_by(self, queryset):
        all_param = (self.request.GET.get("all") or "").strip()
        if all_param in ("1", "true", "True", "yes", "on"):
            return None  # sin paginación
        return self.paginate_by

    def get_queryset(self):
        qs = KardexItem.objects.all()
        q = (self.request.GET.get("q") or "").strip()
        area = (self.request.GET.get("area") or "").strip()
        sentido = (self.request.GET.get("sentido") or "").strip()

        if q:
            qs = qs.filter(Q(descripcion__icontains=q))
        if area:
            qs = qs.filter(area=area)
        if sentido:
            qs = qs.filter(sentido=sentido)

        return qs.order_by("id")  # 1 → último

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            "q": self.request.GET.get("q", ""),
            "area_sel": self.request.GET.get("area", ""),
            "sentido_sel": self.request.GET.get("sentido", ""),
            "all_sel": self.request.GET.get("all", ""),
            "areas": KardexItem.Area.choices,
            "sentidos": KardexItem.Sentido.choices,
            "total": self.get_queryset().count(),
        })
        return ctx


class KardexItemCreateView(RoleRequiredMixin, CreateView):
    model = KardexItem
    form_class = KardexItemForm
    template_name = "kardex/items_form.html"
    success_url = reverse_lazy("estudiantes:kardex_items_listar")
    required_roles = ("director", "secretaria", "secretaría")


class KardexItemUpdateView(RoleRequiredMixin, UpdateView):
    model = KardexItem
    form_class = KardexItemForm
    template_name = "kardex/items_form.html"
    success_url = reverse_lazy("estudiantes:kardex_items_listar")
    required_roles = ("director", "secretaria", "secretaría")


class KardexItemDeleteView(RoleRequiredMixin, DeleteView):
    model = KardexItem
    template_name = "kardex/items_confirmar_eliminar.html"
    success_url = reverse_lazy("estudiantes:kardex_items_listar")
    required_roles = ("director", "secretaria", "secretaría")
