import pytest
from users.serializers import *
from users.views import UserViewSet
from rest_framework.test import APIRequestFactory


@pytest.mark.parametrize('action, expected_serializer', [
        ('register', UserSerializer),
        ('login', LoginSerializer),
        ('resetrequest', ResetrequestSerializer),
        ('reactivate', ResetrequestSerializer),
        ('resetpassword', ResetpasswordSerializer),
        ('change_password', ChangePasswordSerializer),
        ('activate', ActivationSerializer)
        ])

def test_get_serializer_class(action, expected_serializer):
    viewset = UserViewSet()
    viewset.action= action
    assert viewset.get_serializer_class()==expected_serializer
