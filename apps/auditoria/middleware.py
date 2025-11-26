import threading

_local = threading.local()


def set_current_request(request):
  _local.request = request


def get_current_request():
  return getattr(_local, "request", None)


class CurrentRequestMiddleware:
  """
  Guarda el request actual en una variable local al hilo
  para poder usarlo en señales (IP, usuario, navegador).
  """

  def __init__(self, get_response):
    self.get_response = get_response

  def __call__(self, request):
    set_current_request(request)
    response = self.get_response(request)
    set_current_request(None)
    return response
