from django.contrib.auth import get_user_model, authenticate
#from django.utils.translation import ugettext_lazy as _
# For Django V4:
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the users objects"""

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'password', 'name', 'is_active', 'is_limited', 'is_partner', 'is_staff', 'is_superuser')
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}

    # validated_data is all the data that is passed in the serializer in json.
    # Ot os unwind (**) to args in create_user
    # TO CREATE A SUPERUSER: objects.create_superuser..Del 'name'from fields
    # validadted data are all data passed to a serializer(ie a post request)
    def create(self, validated_data):
        """Create a new user with encripted password and returns it"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Setting the password correctly and return it"""
        # Retrives and drops password from the validated_data
        password = validated_data.pop('password', None)
        # validated_data has password nomore
        # Updates instance with the remaining data in validated_data
        user = super().update(instance, validated_data)

        # If the user provides a password
        if password:
            user.set_password(password)
            user.save()

        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user authentication object"""
    email = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    # Data in the serializer are passed to the attrs arg.
    # This permits the date being retrieved inside the function.
    def validate(self, attrs):
        """Validate and authenticate the user"""
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        if not user:
            msg = _('Unable to authenticate with provided credentials')
            raise serializers.ValidationError(msg, code='authentication')

        attrs['user'] = user
        return attrs
