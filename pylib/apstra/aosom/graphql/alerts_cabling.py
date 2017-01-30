import graphene
import graphene.types.json

from .intf_alert import Alert

__all__ = ['CablingAlert']


class CablingAlert(graphene.ObjectType):
    class Meta:
        interfaces = (Alert, )

    class CablingAlertIdentity(graphene.ObjectType):
        obj = graphene.types.json.JSONString(required=True)
        system_id = graphene.String(
            resolver=lambda x, *_: x.obj['system_id'])
        interface = graphene.String(
            resolver=lambda x, *_: x.obj['interface'])

    class CablingAlertExpectation(graphene.ObjectType):
        obj = graphene.types.json.JSONString(required=True)
        nei_name = graphene.String(
            resolver=lambda x, *_: x.obj['neighbor_name'])
        nei_interface = graphene.String(
            resolver=lambda x, *_: x.obj['neighbor_interface'])

    identity = graphene.Field(
        CablingAlertIdentity,
        resolver=lambda x, *_: x.CablingAlertIdentity(
            obj=x.obj['identity']))

    expected = graphene.Field(
        CablingAlertExpectation,
        resolver=lambda x, *_: x.CablingAlertExpectation(
            obj=x.obj['expected']))

    actual = graphene.Field(
        CablingAlertExpectation,
        resolver=lambda x, *_: x.CablingAlertExpectation(
            obj=x.obj['actual']))
