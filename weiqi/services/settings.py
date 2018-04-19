from binascii import a2b_base64
from io import BytesIO

from PIL import Image
from weiqi.services import BaseService, ServiceError


class InvalidImageError(ServiceError):
    pass


class SettingsService(BaseService):
    __service_name__ = 'settings'

    @BaseService.authenticated
    @BaseService.register
    def user_info(self):
        return {
            'email': self.user.email,
            'info_text': self.user.info_text,
            'correspondence_emails': self.user.correspondence_emails
        }

    @BaseService.authenticated
    @BaseService.register
    def save_user_info(self, email, info_text, correspondence_emails):
        self.user.email = email
        self.user.info_text = info_text
        self.user.correspondence_emails = correspondence_emails

    @BaseService.authenticated
    @BaseService.register
    def upload_avatar(self, avatar):
        if not avatar.startswith('data:image/png;base64,'):
            raise InvalidImageError('only png images are supported')

        data = avatar.split(',', 1)[1]
        data = a2b_base64(data)
        img = Image.open(BytesIO(data))
        width, height = img.size

        if width != 256 or height != 256:
            raise InvalidImageError('image size must be 256x256')

        large = BytesIO()
        img.save(large, format='JPEG', quality=90,
                 optimize=True, progressive=True)

        small = BytesIO()
        img.thumbnail((64, 64))
        img.save(small, format='JPEG', quality=90,
                 optimize=True, progressive=True)

        self.user.avatar_large = large.getvalue()
        self.user.avatar = small.getvalue()

    @BaseService.authenticated
    @BaseService.register
    def delete_avatar(self):
        self.user.avatar = None
        self.user.avatar_large = None

    @BaseService.authenticated
    @BaseService.register
    def change_password(self, password):
        self.user.set_password(password)
