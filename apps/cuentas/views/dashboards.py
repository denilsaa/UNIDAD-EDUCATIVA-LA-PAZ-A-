from django.shortcuts import render
from apps.cuentas.decorators import role_required

@role_required("padre")
def padre_dashboard(request):
    return render(request, "dashboard/padre_dashboard.html")

@role_required("regente")
def regente_dashboard(request):
    return render(request, "dashboard/regente_dashboard.html")

@role_required("secretaria","secretaría")
def secretaria_dashboard(request):
    return render(request, "dashboard/secretaria_dashboard.html")
