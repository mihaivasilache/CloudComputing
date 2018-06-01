from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.shortcuts import render_to_response
from django.views import View
from django.shortcuts import redirect
from django.template.context import RequestContext
from django.contrib.auth.decorators import login_required

class HelpView(View):

	template_name = 'help.html'    
	
	def get(self, request, *args, **kwargs):        
		return render(request, self.template_name)
