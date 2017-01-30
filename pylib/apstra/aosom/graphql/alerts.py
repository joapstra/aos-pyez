
import jmespath
import graphene
from graphql.error import GraphQLError

from .intf_alert import Alert
from .alerts_interface import InterfaceAlert
from .alerts_cabling import CablingAlert
from .alerts_route import RouteAlert
from .alerts_bgp import BgpAlert


class AnyAlert(graphene.ObjectType):
    class Meta:
        interfaces = (Alert, )


AlertTypeCls = {
    'bgp': BgpAlert,
    'cabling': CablingAlert,
    'interface': InterfaceAlert,
    'route': RouteAlert
}


class AlertTypeValidator(graphene.String):
    @staticmethod
    def parse_literal(ast):
        if ast.value not in AlertTypeCls.keys():
            raise GraphQLError(
                message="unknown AlertType value: '%s'" % ast.value)
        return ast.value


class AlertItem(graphene.Union):
    class Meta:
        types = [AnyAlert] + AlertTypeCls.values()


def _filter_alerts(alerts, oargs):
    filter_fields = {
        'alertType': "alert_type=='{}'",
        'role': "role=='{}'"
    }

    expr_l = list()
    for k, v in oargs.items():
        expr_l.append(filter_fields[k].format(v))

    jfind = jmespath.compile(' && '.join(expr_l))

    return [each for each in alerts if jfind.search(each.value)]


class AlertsQuery(object):
    class Qschema(graphene.ObjectType):
        alerts = graphene.List(
            AlertItem,
            alertType=AlertTypeValidator(),
            role=graphene.String()
        )

        def resolve_alerts(self, oargs, context, info):
            owner = context['owner']

            alerts = _filter_alerts(owner, oargs) if oargs else owner

            return [
                AlertTypeCls.get(
                    alert.value['alert_type'], AnyAlert)(obj=alert.value)
                for alert in alerts
            ]

    def __init__(self, owner):
        self.owner = owner
        self.schema = graphene.Schema(query=self.Qschema)

    def __call__(self, query, **kwargs):
        return self.schema.execute(
            query, context_value=dict(
                owner=self.owner
            ))
