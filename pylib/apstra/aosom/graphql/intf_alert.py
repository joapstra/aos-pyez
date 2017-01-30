import iso8601
import graphene
import graphene.types.json
import graphene.types.datetime


class Alert(graphene.Interface):
    obj = graphene.types.json.JSONString()

    id = graphene.ID(
        resolver=lambda x, *_: x.obj['id'])
    createdAt = graphene.types.datetime.DateTime(
        resolver=lambda x, *_: iso8601.parse_date(x.obj['created_at']))
    modifiedAt = graphene.types.datetime.DateTime(
        resolver=lambda x, *_: iso8601.parse_date(x.obj['last_modified_at']))

    alertType = graphene.String(
        resolver=lambda x, *_: x.obj['alert_type'])
    severity = graphene.String(
        resolver=lambda x, *_: x.obj['severity'])
    role = graphene.String(
        resolver=lambda x, *_: x.obj['role'])
