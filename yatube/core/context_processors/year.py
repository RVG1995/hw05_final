from django.utils import timezone


def year(request):
    current = timezone.now().strftime("%Y")
    return {"year": int(current)}
