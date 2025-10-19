# apps/estudiantes/views/kardex_item.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q

from apps.estudiantes.models.kardex_item import KardexItem
from apps.estudiantes.forms import KardexItemForm


# --- Permisos por rol (ajusta si usas otra lógica)
def es_autorizado(user):
    rol = (getattr(getattr(user, "rol", None), "nombre", "") or "").lower()
    return any(r in rol for r in ("director", "regente", "secretaria", "secretaría"))


def auth_decorators():
    return [login_required, user_passes_test(es_autorizado)]


@method_decorator(auth_decorators(), name="dispatch")
class KardexItemListView(ListView):
    model = KardexItem
    template_name = "kardex/items_lista.html"
    context_object_name = "items"
    paginate_by = 20  # paginación por defecto

    # Permite desactivar paginación cuando viene ?all=1
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

        # 🔹 Orden 1 → último: por ID ascendente
        return qs.order_by("id")

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


@method_decorator(auth_decorators(), name="dispatch")
class KardexItemCreateView(CreateView):
    model = KardexItem
    form_class = KardexItemForm
    template_name = "kardex/items_form.html"
    success_url = reverse_lazy("estudiantes:kardex_items_listar")


@method_decorator(auth_decorators(), name="dispatch")
class KardexItemUpdateView(UpdateView):
    model = KardexItem
    form_class = KardexItemForm
    template_name = "kardex/items_form.html"
    success_url = reverse_lazy("estudiantes:kardex_items_listar")


@method_decorator(auth_decorators(), name="dispatch")
class KardexItemDeleteView(DeleteView):
    model = KardexItem
    template_name = "kardex/items_confirmar_eliminar.html"
    success_url = reverse_lazy("estudiantes:kardex_items_listar")
