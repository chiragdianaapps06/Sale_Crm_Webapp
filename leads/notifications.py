import firebase_admin
from firebase_admin import messaging

def send_push_notification(device_token, title, body):
    try:
        # Create the message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            token=device_token,
        )
        
        # Send the message
        response = messaging.send(message)
        print(f"Successfully sent message: {response}")
        return response
    except Exception as e:
        print(f"Error sending message: {str(e)}")
        return None
