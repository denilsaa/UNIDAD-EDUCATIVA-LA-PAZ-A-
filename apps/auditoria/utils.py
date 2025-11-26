from typing import Optional
from django.http import HttpRequest

from .middleware import get_current_request


def get_request() -> Optional[HttpRequest]:
  """Devuelve el request actual almacenado en el middleware."""
  return get_current_request()


def get_ip_ua_from_request(request: Optional[HttpRequest]):
  """Obtiene IP y User-Agent desde el request."""
  if not request:
    return None, ""

  xff = request.META.get("HTTP_X_FORWARDED_FOR")
  if xff:
    ip = xff.split(",")[0].strip()
  else:
    ip = request.META.get("REMOTE_ADDR")

  ua = request.META.get("HTTP_USER_AGENT", "")[:255]
  return ip, ua
