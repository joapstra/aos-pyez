import json
import graphene
import graphene.types.json
import jmespath

from apstra.aosom.session import Session

class SystemNodeFacts(graphene.ObjectType):
    obj = graphene.types.json.JSONString()

    ipAddr = graphene.String(
        description='system management IP address',
        resolver=lambda x, *_: x.obj['mgmt_ipaddr'])

    macAddr = graphene.String(
        description='system management interface MACAddress',
        resolver=lambda x, *_: x.obj['mgmt_macaddr'])

    serialNumber = graphene.String(
        description='system serial-number',
        resolver=lambda x, *_: x.obj['serial_number'])

    vendor = graphene.String(
        description='system vendor name',
        resolver=lambda x, *_: x.obj['vendor'])


class SystemNode(graphene.ObjectType):
    obj = graphene.types.json.JSONString()

    id = graphene.ID(
        resolver=lambda x, *_: x.obj['device_key'])

    facts = graphene.Field(
        SystemNodeFacts,
        resolver=lambda x, *_: SystemNodeFacts(obj=x.obj['facts']))


class BlueprintNode(graphene.ObjectType):
    obj = graphene.types.json.JSONString()
    name = graphene.String(required=True)

    hostname = graphene.String()
    role = graphene.String()
    system_id = graphene.String()
    hcl_id = graphene.String()
    deploy_mode = graphene.String()

    system = graphene.Field(SystemNode)

    def resolve_role(self, oargs, context, info):
        return self.obj['role']

    def resolve_name(self, oargs, context, info):
        return self.obj['display_name']

    def resolve_hostname(self, oargs, context, info):
        return self.obj['hostname']

    def resolve_system(self, oargs, context, info):
        aos = context['aos']
        sys_id = self.obj['system_id']
        if sys_id not in aos.Devices:
            return None

        return SystemNode(obj=aos.Devices[sys_id].value)


class LinkEndpoint(graphene.ObjectType):
    obj = graphene.types.json.JSONString()
    node_name = graphene.String()
    interface_name = graphene.String()
    ip_addr = graphene.String()
    ep_mode = graphene.String()
    ep_type = graphene.String()

    node = graphene.Field(BlueprintNode)
    system = graphene.Field(SystemNode)

    @graphene.resolve_only_args
    def resolve_node_name(self):
        return self.obj['display_name']

    @graphene.resolve_only_args
    def resolve_interface_name(self):
        return self.obj['interface']

    @graphene.resolve_only_args
    def resolve_ip_addr(self):
        return self.obj['ip']

    @graphene.resolve_only_args
    def resolve_ep_mode(self):
        return self.obj['mode']

    @graphene.resolve_only_args
    def resolve_ep_type(self):
        return self.obj['type']

    def resolve_node(self, args, context, info):
        cts = context['contents']

        return BlueprintNode(obj=filter(
            lambda x: x['display_name'] == self.obj['display_name'],
            cts['system']['nodes'])[0])

    def resolve_system(self, args, context, info):
        nodes = context['contents']['system']['nodes']
        this_node = filter(lambda x: x['display_name'] == self.obj['display_name'], nodes)[0]
        sys_id = this_node['system_id']
        if not sys_id:
            return None

        aos = context['aos']
        return SystemNode(obj=aos.Devices[sys_id].value)



class CableLink(graphene.ObjectType):
    name = graphene.String()
    role = graphene.String()
    endpoints = graphene.Field(
        graphene.List(lambda: LinkEndpoint),
        jpath=graphene.String())

    def __init__(self, obj):
        self.obj = obj
        super(CableLink, self).__init__()

    @graphene.resolve_only_args
    def resolve_name(self):
        return self.obj['display_name']

    @graphene.resolve_only_args
    def resolve_role(self):
        return self.obj['role']

    def resolve_endpoints(self, oargs, context, info):
        jpath = oargs.get('jpath') or '[]'

        return [
            LinkEndpoint(obj=obj)
            for obj in jmespath.search(jpath, self.obj['endpoints'])
        ]


aos = Session('aos-server')
aos.login()
bp = aos.Blueprints['demo-vpod-l2']


def res_dumps(res):
    print json.dumps(res.data, indent=4)


def test_1():

    class QueryLinks(graphene.ObjectType):
        links = graphene.Field(
            graphene.List(lambda: CableLink),
            role=graphene.String()
        )

        def resolve_links(self, oargs, context, info):
            contents = context.get('contents')
            all_objs = contents['system']['links']

            def _no_filter(obj):
                return True

            if 'role' in oargs:
                def _role_filter(obj):
                    return obj['role'] == oargs['role']

                _oarg_filter = _role_filter
            else:
                _oarg_filter = _no_filter

            return [CableLink(obj=obj) for obj in all_objs
                    if _oarg_filter(obj)]

    qry = """
    {
        links(role: "spine_leaf") {
            name
            endpoints {
                nodeName
                interfaceName
            }
        }
    }
    """

    return graphene.Schema(query=QueryLinks).execute(
        qry,
        context_value=dict(
            aos=aos, blueprint=bp,
            contents=bp.contents)
    )

def query_links_schema():
    class Query(graphene.ObjectType):

        links = graphene.Field(
            graphene.List(lambda : CableLink),
            jpath=graphene.String()
        )

        def resolve_links(self, oargs, context, info):
            return [
                CableLink(obj=obj)
                for obj in jmespath.search(
                    oargs.get('jpath') or '[]',
                    context['contents']['system']['links'])]

    return graphene.Schema(query=Query)


def test_2():

    qry = """
    {
        links(jpath: "[?role=='spine_leaf']") {
            name
            endpoints {
                system {
                    id
                }
                interfaceName
            }
        }
    }
    """

    schema = query_links_schema()
    return schema.execute(
        qry,
        context_value=dict(
            aos=aos, blueprint=bp,
            contents=bp.contents)
    )



def query_system_schema():
    class Query(graphene.ObjectType):
        systems = graphene.Field(
            graphene.List(lambda : SystemNode),
            ipAddr=graphene.String(),
            jpath=graphene.String())

        def resolve_systems(self, oargs, context, info):
            sobjs = [dev.value for dev in aos.Devices]

            def jpath():
                if 'ipAddr' in oargs:
                    return "[?facts.mgmt_ipaddr == '{}']".format(oargs['ipAddr'])

                if 'jpath' in oargs:
                    return oargs['jpath']

                return '[]'

            return [
                SystemNode(obj=obj)
                for obj in jmespath.search(jpath(), sobjs)
            ]

    return graphene.Schema(query=Query)


def test_3():

    qry = """
    query FindByIpAddr($ipAddr: String!) {
        systems(ipAddr: $ipAddr) {
            id
            facts {
                obj
            }
        }
    }
    """

    qry = """
    {
        systems(jpath: "[?facts.serial_number == '080027809314']") {
            id
            facts {
                vendor
                ipAddr
                macAddr
            }
        }
    }
    """

    return query_system_schema().execute(
        qry,
        variable_values=dict(ipAddr='192.168.60.13'),
        context_value=dict(aos=aos)
    )
