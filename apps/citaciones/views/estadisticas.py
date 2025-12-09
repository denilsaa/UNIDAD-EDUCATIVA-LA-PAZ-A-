# apps/citaciones/views/estadisticas.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from apps.citaciones.services.mm1_simulator import (
    simulacion_mm1,
    distribucion_por_estado,
)


@login_required
def estadisticas_teoria_colas(request):
    # 1) Métricas M/M/1 (λ, μ, ρ, Wq, Ws)
    mm1 = simulacion_mm1(dias=7)

    # 2) Distribución de citaciones por estado
    dist = distribucion_por_estado()
    total_cit = sum(dist["data"]) or 1

    estados = []
    for label, count in zip(dist["labels"], dist["data"]):
        estados.append({
            "label": label,
            "count": count,
            "pct": round(count * 100.0 / total_cit, 1),
        })

    # 3) Porcentajes para las barras “gráfico”
    lam = mm1.get("lambda") or 0
    mu = mm1.get("mu") or 0
    rho = mm1.get("rho") or 0

    max_cap = max(lam, mu, 0.0001)  # evitar división por cero

    lambda_pct = lam / max_cap * 100.0
    mu_pct = mu / max_cap * 100.0

    rho_clamp = max(0.0, min(1.0, rho))
    rho_pct = rho_clamp * 100.0
    libre_pct = max(0.0, 100.0 - rho_pct)

    context = {
        "mm1": mm1,
        "lambda_pct": lambda_pct,
        "mu_pct": mu_pct,
        "rho_pct": rho_pct,
        "libre_pct": libre_pct,
        "estados": estados,
    }
    return render(request, "citaciones/estadisticas_teoria_colas.html", context)
