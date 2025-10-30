# apps/cursos/views/cursos.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.db.models import Q, ForeignKey
from django.db import transaction, connection
from django.apps import apps as django_apps

from apps.cursos.models import Curso
from apps.cursos.forms import CursoForm

# 🔒 utilidades de rol
from apps.cuentas.decorators import role_required
from apps.cuentas.roles import es_director, es_regente


# =========================================================
#   Centinelas (para "sin curso" sin cambiar modelos/BD)
# =========================================================
SENT_NIVEL = "SIN"
SENT_PARALELO = "—"

def _is_curso_centinela(curso):
    return getattr(curso, "nivel", None) == SENT_NIVEL and getattr(curso, "paralelo", None) == SENT_PARALELO


def _ensure_regente_role():
    Rol = django_apps.get_model("cuentas", "Rol")
    rol = Rol.objects.filter(nombre__iexact="Regente").first()
    if not rol:
        rol = Rol.objects.create(nombre="Regente")
    return rol


def _get_or_create_regente_centinela():
    """
    Usuario centinela 'SIN REGENTE' con rol=Regente y valores dummy
    para campos NOT NULL si existen.
    """
    Usuario = django_apps.get_model("cuentas", "Usuario")
    rol_regente = _ensure_regente_role()

    correo = "sin.regente@ue-lapaz.internal"
    obj = Usuario.objects.filter(email=correo).first()
    if obj:
        if getattr(obj, "rol_id", None) != rol_regente.id:
            obj.rol = rol_regente
            obj.save(update_fields=["rol"])
        return obj

    defaults = {
        "nombres": "SIN",
        "apellidos": "REGENTE",
        "is_activo": False,
        "rol": rol_regente,
    }
    # Rellenar campos NOT NULL habituales si existen
    for fname, fval in [("ci", "SIN-REGENTE-000"), ("username", "sin_regente")]:
        try:
            field = Usuario._meta.get_field(fname)
            if not field.null:
                defaults[fname] = fval
        except Exception:
            pass
    # Password (si existe el campo)
    try:
        Usuario._meta.get_field("password")
        defaults.setdefault("password", "!")
    except Exception:
        pass

    obj, _ = Usuario.objects.get_or_create(email=correo, defaults=defaults)
    return obj


def _get_or_create_curso_sin_curso():
    """
    Crea/obtiene curso centinela 'SIN/—' con regente centinela (evita regente_id NULL).
    """
    cont = Curso.objects.filter(nivel=SENT_NIVEL, paralelo=SENT_PARALELO).first()
    if cont:
        return cont
    regente_centinela = _get_or_create_regente_centinela()
    return Curso.objects.create(nivel=SENT_NIVEL, paralelo=SENT_PARALELO, regente=regente_centinela)


# =========================================================
#   Descubrir y mover TODAS las FKs -> Curso (genérico)
# =========================================================
def _models_fk_to_curso():
    """
    Lista [(ModelClass, field)] de TODOS los ForeignKey que apuntan a Curso.
    """
    result = []
    for model in django_apps.get_models():
        for field in model._meta.get_fields():
            if isinstance(field, ForeignKey) and getattr(field.remote_field, "model", None) is Curso:
                result.append((model, field))
    return result


def _move_fk_to_contenedor(model_cls, fk_field, curso_origen, curso_destino):
    """
    Mueve registros model_cls con fk_field==curso_origen -> curso_destino.
    1) ORM .update()
    2) Fallback SQL crudo (db_table + column real)
    Devuelve cantidad de filas afectadas.
    """
    field_name = fk_field.name  # nombre del atributo en el modelo
    # Intento ORM
    try:
        return model_cls.objects.filter(**{field_name: curso_origen}).update(**{field_name: curso_destino})
    except Exception:
        pass
    # Fallback SQL
    try:
        table = model_cls._meta.db_table
        col = fk_field.column  # nombre de columna en la BD (p.ej. curso_id)
        with connection.cursor() as cur:
            cur.execute(
                f"UPDATE `{table}` SET `{col}` = %s WHERE `{col}` = %s",
                [curso_destino.id, curso_origen.id],
            )
            return cur.rowcount or 0
    except Exception:
        return 0


def _any_left_pointing(model_cls, fk_field, curso_origen):
    """
    ¿Queda alguna fila apuntando a curso_origen?
    """
    try:
        return model_cls.objects.filter(**{fk_field.name: curso_origen}).exists()
    except Exception:
        try:
            table = model_cls._meta.db_table
            col = fk_field.column
            with connection.cursor() as cur:
                cur.execute(
                    f"SELECT 1 FROM `{table}` WHERE `{col}` = %s LIMIT 1",
                    [curso_origen.id],
                )
                row = cur.fetchone()
                return bool(row)
        except Exception:
            return True  # conservador


# ============================
#   SOLO DIRECTOR
# ============================

@role_required("director")
def lista_cursos(request):
    q = (request.GET.get("q") or "").strip()
    cursos = (Curso.objects
              .exclude(nivel=SENT_NIVEL, paralelo=SENT_PARALELO)  # ⬅️ ocultar centinela
              .order_by("nivel", "paralelo"))
    if q:
        cursos = cursos.filter(Q(nivel__icontains=q) | Q(paralelo__icontains=q))
    return render(request, "cursos/lista_cursos.html", {"cursos": cursos, "q": q})


@role_required("director")
def crear_curso(request):
    if request.method == "POST":
        form = CursoForm(request.POST)
        if form.is_valid():
            curso = form.save()
            messages.success(request, "Curso creado correctamente.")
            return redirect(reverse("cursos:ver_curso", args=[curso.id]))
        messages.error(request, "Por favor corrija los errores.")
    else:
        form = CursoForm()
    return render(request, "cursos/crear_curso.html", {"form": form})


@login_required
def ver_curso(request, curso_id):
    """
    Director: puede ver cualquier curso.
    Regente: solo puede ver si es regente del curso.
    Otros roles: 403.
    """
    curso = get_object_or_404(Curso, id=curso_id)

    # 🔒 Bloquear acceso al centinela en UI
    if _is_curso_centinela(curso):
        messages.info(request, "El curso ‘SIN CURSO’ es de sistema y no se muestra.")
        return redirect(reverse("cursos:lista_cursos"))

    if es_director(request.user):
        pass
    elif es_regente(request.user):
        if getattr(curso, "regente_id", None) != request.user.id:
            return render(request, "403.html", status=403)
    else:
        return render(request, "403.html", status=403)

    return render(request, "cursos/ver_curso.html", {"curso": curso})


@role_required("director")
def editar_curso(request, curso_id):
    curso = get_object_or_404(Curso, id=curso_id)

    # 🔒 No permitir editar el centinela
    if _is_curso_centinela(curso):
        messages.error(request, "El curso ‘SIN CURSO’ no se puede editar.")
        return redirect(reverse("cursos:lista_cursos"))

    if request.method == "POST":
        form = CursoForm(request.POST, instance=curso)
        if form.is_valid():
            form.save()
            messages.success(request, "Curso actualizado correctamente.")
            return redirect(reverse("cursos:ver_curso", args=[curso.id]))
        messages.error(request, "Por favor corrija los errores.")
    else:
        form = CursoForm(instance=curso)
    return render(request, "cursos/editar_curso.html", {"form": form, "curso": curso})


@role_required("director")
def eliminar_curso(request, curso_id):
    """
    Elimina un curso:
    - Si es centinela: ocultar/bloquear (solo se permite eliminar si no tiene referencias).
    - Si es normal: mover TODAS las FKs->Curso al centinela y luego borrar.
    """
    curso = get_object_or_404(Curso, id=curso_id)

    # 🚫 No permitir eliminar el centinela si aún tiene referencias
    if _is_curso_centinela(curso):
        # ¿Quedan referencias al centinela?
        fk_targets = _models_fk_to_curso()
        sigue_referenciado = []
        for model_cls, fk_field in fk_targets:
            if _any_left_pointing(model_cls, fk_field, curso):
                sigue_referenciado.append(f"{model_cls.__name__}.{fk_field.name}")

        if sigue_referenciado:
            messages.error(
                request,
                "No puedes eliminar el curso ‘SIN CURSO’ porque aún tiene referencias: "
                + ", ".join(sigue_referenciado)
            )
            return redirect(reverse("cursos:lista_cursos"))

        # Si no tiene referencias, permitir borrarlo con confirmación POST
        if request.method == "POST":
            curso.delete()
            messages.success(request, "Curso ‘SIN CURSO’ eliminado (no tenía referencias).")
            return redirect(reverse("cursos:lista_cursos"))

        messages.warning(request, "Confirmación: ¿Eliminar ‘SIN CURSO’? (solo si no tiene referencias)")
        return render(request, "cursos/eliminar_curso.html", {"curso": curso})

    # 🔽 Curso normal: proceder a mover y borrar
    if request.method == "POST":
        with transaction.atomic():
            # 1) Asegurar centinelas
            _get_or_create_regente_centinela()
            contenedor = _get_or_create_curso_sin_curso()

            # 2) Encontrar y mover TODAS las FKs->Curso
            fk_targets = _models_fk_to_curso()
            for model_cls, fk_field in fk_targets:
                _move_fk_to_contenedor(model_cls, fk_field, curso, contenedor)

            # 3) Verificar que ya no haya nada apuntando
            aun_bloquea = []
            for model_cls, fk_field in fk_targets:
                if _any_left_pointing(model_cls, fk_field, curso):
                    aun_bloquea.append(f"{model_cls.__name__}.{fk_field.name}")

            if aun_bloquea:
                messages.error(
                    request,
                    "No se pudo eliminar el curso porque aún hay referencias en: "
                    + ", ".join(aun_bloquea)
                    + ". Revisa triggers, constraints o FKs no estándar."
                )
                return redirect(reverse("cursos:ver_curso", args=[curso.id]))

            # 4) Borrar el curso original
            curso.delete()

        messages.success(request, "Curso eliminado. Dependencias movidas a ‘SIN CURSO’.")
        return redirect(reverse("cursos:lista_cursos"))

    return render(request, "cursos/eliminar_curso.html", {"curso": curso})


# ============================
#   REGENTE: SOLO SUS CURSOS
# ============================

@role_required("regente")
def mis_cursos_regente(request):
    """
    Listado de cursos del regente autenticado.
    (El centinela no saldrá aquí porque su regente es el usuario centinela.)
    """
    cursos = (
        Curso.objects
        .filter(regente_id=request.user.id)
        .order_by("nivel", "paralelo")
    )
    return render(request, "cursos/mis_cursos.html", {"cursos": cursos})
