from django.utils.translation import ugettext as _
from rest_framework_jwt.serializers import *

from users.models import Users


class CusTomSerializer(JSONWebTokenSerializer, Serializer):

    def __init__(self, *args, **kwargs):
        """
        Dynamically add the USERNAME_FIELD to self.fields.
        """
        super(CusTomSerializer, self).__init__(*args, **kwargs)
        self.fields["username"] = serializers.CharField()  # 账户
        self.fields['password'] = serializers.CharField()  # 密码
        # self.fields['remember'] = serializers.IntegerField(default=60, allow_null=True)  # 过期时间

    def validate(self, attrs):
        credentials = {
            'username': attrs.get('username'),
            'password': attrs.get('password'),
        }
        if all(credentials.values()):
            try:
                user = Users.objects.get(username=credentials.get('username'))  # 自己新建的model，不是django里的User
            except Users.DoesNotExist:
                msg = _('the validate code is error')
                raise serializers.ValidationError(msg)
            if user:
                # exp = datetime.utcnow() + timedelta(seconds=credentials.get('remember'))  # 过期时间
                payload = jwt_payload_handler(user)
                return {
                    'token': jwt_encode_handler(payload),
                    'user': user
                }
            else:
                msg = _('Unable to log in with provided credentials.')
                raise serializers.ValidationError(msg)
        else:
            msg = _('Must include "{username_field}" and "password".')
            raise serializers.ValidationError(msg)
