import graphene
import graphene.types.json

from .intf_alert import Alert

__all__ = ['BgpAlert']


class BgpAlert(graphene.ObjectType):
    class Meta:
        interfaces = (Alert, )

    class BgpAlertIdentity(graphene.ObjectType):
        obj = graphene.types.json.JSONString(required=True)
        system_id = graphene.String(
            resolver=lambda x, *_: x.obj['system_id'])
        dst_ip = graphene.String(
            resolver=lambda x, *_: x.obj['destination_ip'])
        dst_asn = graphene.String(
            resolver=lambda x, *_: x.obj['destination_asn'])
        src_ip = graphene.String(
            resolver=lambda x, *_: x.obj['source_ip'])
        src_asn = graphene.String(
            resolver=lambda x, *_: x.ojb['source_asn'])

    class BgpAlertExpectation(graphene.ObjectType):
        obj = graphene.types.json.JSONString(required=True)
        value = graphene.String(
            resolver=lambda x, *_: x.obj['value'])

    identity = graphene.Field(
        BgpAlertIdentity,
        resolver=lambda x, *_: x.BgpAlertIdentity(
            obj=x.obj['identity']))

    expected = graphene.Field(
        BgpAlertExpectation,
        resolver=lambda x, *_: x.BgpAlertExpectation(
            obj=x.obj['expected']))

    actual = graphene.Field(
        BgpAlertExpectation,
        resolver=lambda x, *_: x.BgpAlertExpectation(
            obj=x.obj['actual']))
