import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stocksync.settings")
django.setup()

from accounts.models import User


def superuser():
    email = os.getenv('SUPERUSER_EMAIL')
    password = os.getenv('SUPERUSER_PASSWORD')
    username = os.getenv('SUPERUSER_USERNAME')
    first_name = os.getenv('SUPERUSER_FIRSTNAME')
    last_name = os.getenv('SUPERUSER_LASTNAME')
    
    if email and password:
        user = User.objects.create_superuser(email=email, username=username, first_name=first_name, last_name=last_name)
        user.set_password(password)
        user.save()
        return {
            'statusCode': 200,
            'body': 'Superuser created successfully'
        }
    else:
        return {
            'statusCode': 500,
            'body': 'Error: SUPERUSER_EMAIL or SUPERUSER_PASSWORD environment variables are not set.'
        }

def main():
    superuser()
if __name__ == '__main__':
    main()
