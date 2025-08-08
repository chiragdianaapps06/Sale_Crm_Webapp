from rest_framework.renderers import BaseRenderer
from rest_framework import status
import json
class CustomRenderer(BaseRenderer):
    media_type="application/json"
    format='json'
    charset='utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        response=renderer_context.get('response',None)
        status_code=response.status_code if response else 200

        message=self.get_default_message(status_code)
        final_data=data

        if isinstance(data,dict):
            message=data.pop('message',message)
            final_data=data.pop('data',data) 
        elif isinstance(data,(list,str,type(None))):
            final_data=data

        else:
            final_data=str(data)

        wrapped={
            'status':status_code,
            'message':message,
            'data':final_data
        }

        return json.dumps(wrapped).encode(self.charset)

    def get_default_message(self,status_code):
        default_messages = {
            status.HTTP_200_OK: "Success",
            status.HTTP_201_CREATED: "Created successfully",
            status.HTTP_204_NO_CONTENT: "No content",
            status.HTTP_400_BAD_REQUEST: "Bad request",
            status.HTTP_401_UNAUTHORIZED: "Unauthorized",
            status.HTTP_403_FORBIDDEN: "Forbidden",
            status.HTTP_404_NOT_FOUND: "Not found",
            status.HTTP_500_INTERNAL_SERVER_ERROR: "Internal server error"
        }
        return default_messages.get(status_code,"")