import graphene
import graphene.types.json

from .intf_alert import Alert

__all__ = ['RouteAlert']


class RouteAlert(graphene.ObjectType):
    class Meta:
        interfaces = (Alert, )

    class RouteAlertIdentity(graphene.ObjectType):
        obj = graphene.types.json.JSONString(required=True)
        system_id = graphene.String(
            resolver=lambda x, *_: x.obj['system_id'])
        dst_ip = graphene.String(
            resolver=lambda x, *_: x.obj['destination_ip'])

    class RouteAlertExpectation(graphene.ObjectType):
        obj = graphene.types.json.JSONString(required=True)
        value = graphene.String(
            resolver=lambda x, *_: x.obj['value'])

    identity = graphene.Field(
        RouteAlertIdentity,
        resolver=lambda x, *_: x.RouteAlertIdentity(
            obj=x.obj['identity']))

    expected = graphene.Field(
        RouteAlertExpectation,
        resolver=lambda x, *_: x.RouteAlertExpectation(
            obj=x.obj['expected']))

    actual = graphene.Field(
        RouteAlertExpectation,
        resolver=lambda x, *_: x.RouteAlertExpectation(
            obj=x.obj['actual']))
