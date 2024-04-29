import json
import os
from werkzeug.wrappers import Request, Response, ResponseStream

class middleware():
    '''
    Simple WSGI middleware
    '''

    def __init__(self, app):
        self.app = app

    ignore_paths = ['/logs', '/clear','/fetch_logs']
    def __call__(self, environ, start_response):
        request = Request(environ)
        
        
        
        return self.app(environ, start_response)
        
        for path in self.ignore_paths:
            if request.path == path:
                return self.app(environ, start_response)
        
        
        #check if 'api-key' is in the request headers
        if 'api-key' not in request.headers:
            res = Response(json.dumps ({
                "error": "Unauthorized",
                "message": "API Key is required"
                    }), status=401, mimetype='application/json')
            
            return res(environ, start_response)
        
        
        
        
        # Check if the request is authorized
        if request.headers['api-key'] != os.getenv('MARINE_API_KEY'):
            res = Response(json.dumps ({
                "error": "Unauthorized",
                "message": "Invalid API Key"
                    }), status=401, mimetype='application/json')
            
            return res(environ, start_response)

        #response as json
      
    
        return self.app(environ, start_response)