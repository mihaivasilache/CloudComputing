from django.http import HttpResponse
from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.views import View
from django.shortcuts import redirect  
from django.shortcuts import render_to_response
from django.template.context import RequestContext
import json
from django.conf import settings
from tweepy.parsers import Parser
from django.utils.datastructures import MultiValueDictKeyError


class LoginView(View):
    template_name = "login_2.html"
    
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
        

    def post(self, request, **kwargs):     
    	username = request.POST['username']
    	password = request.POST['password']
    	user = authenticate(request, username=username, password=password)
    	if user is not None:
            login(request, user)
            return render(request, "home.html")
    	else:
            return render(request, self.template_name)
