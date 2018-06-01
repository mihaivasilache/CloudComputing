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


class MyAccountView(View):
    template_name = "my_account.html"
    
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
        
   
