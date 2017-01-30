import graphene
import graphene.types.json

from .intf_alert import Alert

__all__ = ['InterfaceAlert']


class InterfaceAlert(graphene.ObjectType):
    class Meta:
        interfaces = (Alert, )

    class InterfaceAlertIdentity(graphene.ObjectType):
        obj = graphene.types.json.JSONString(required=True)
        system_id = graphene.String(
            resolver=lambda x, *_: x.obj['system_id'])
        interface = graphene.String(
            resolver=lambda x, *_: x.obj['interface'])

    class InterfaceAlertExpectation(graphene.ObjectType):
        obj = graphene.types.json.JSONString(required=True)
        value = graphene.String(
            resolver=lambda x, *_: x.obj['value'])

    identity = graphene.Field(
        InterfaceAlertIdentity,
        resolver=lambda x, *_: x.InterfaceAlertIdentity(
            obj=x.obj['identity']))

    expected = graphene.Field(
        InterfaceAlertExpectation,
        resolver=lambda x, *_: x.InterfaceAlertExpectation(
            obj=x.obj['expected']))

    actual = graphene.Field(
        InterfaceAlertExpectation,
        resolver=lambda x, *_: x.InterfaceAlertExpectation(
            obj=x.obj['actual']))
