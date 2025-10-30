from django.shortcuts import render
from django.http import JsonResponse
from .interpreter_engine import PolyLangInterpreter

def index(request):
    return render(request, 'index.html')

def execute_code(request):
    if request.method == 'POST':
        code = request.POST.get('code', '')
        interpreter = PolyLangInterpreter()
        result = interpreter.run(code)
        return JsonResponse({'result': result})
    return JsonResponse({'result': 'Invalid request'})
