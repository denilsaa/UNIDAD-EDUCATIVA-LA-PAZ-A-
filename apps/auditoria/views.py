from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Q

from .models import StudentLog


@login_required
def historial_estudiantes(request):
  # Si quieres limitar SOLO director, descomenta esto y ajusta al nombre de rol:
  # role = (getattr(request.user.rol, "nombre", "") or "").lower()
  # if role != "director":
  #   return HttpResponseForbidden("No tienes permiso para ver esta página.")

  q = (request.GET.get("q") or "").strip()

  logs = StudentLog.objects.select_related("usuario", "estudiante")

  if q:
    logs = logs.filter(
      Q(usuario__username__icontains=q)
      | Q(usuario__nombre__icontains=q)
      | Q(estudiante__nombres__icontains=q)
      | Q(estudiante__apellidos__icontains=q)
      | Q(descripcion__icontains=q)
      | Q(ip__icontains=q)
    )

  logs = logs.order_by("-creado_en")[:500]  # últimos 500

  ctx = {
    "logs": logs,
    "q": q,
  }
  return render(request, "auditoria/historial_estudiantes.html", ctx)
