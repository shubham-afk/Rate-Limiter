from django.http import JsonResponse


def health(request):
    return JsonResponse({"status": "ok"})


def data(request):
    """A deliberately small upstream stand-in protected by middleware."""
    return JsonResponse({"data": {"message": "Dummy protected response"}})
