import json
import jmespath
from apstra.aosom.session import Session

aos = Session('aos-server')
aos.login()

def dump(res):
    if res.errors:
        import pdb
        pdb.set_trace()
        return

    print json.dumps(res.data, indent=3)


def test_1():
    results = aos.Alerts.query("""
    {
        alerts {
            ... on Alert {
                id
                alertType
                role
                severity
            }
            ... on InterfaceAlert {
                identity {
                    systemId
                    interface
                }
            }
            ... on RouteAlert {
                identity {
                    dstIp
                }
            }
            ... on CablingAlert {
                identity {
                    systemId
                    interface
                }
                expected {
                    neiName
                    neiInterface
                }
                actual {
                    neiName
                    neiInterface
                }
            }
        }
    }
    """)

    dump(results)
    return results


def test_2():
    results = aos.Alerts.query("""
    {
        alerts(alertType: "interface", role: "spine_leaf") {
            ... on Alert {
                id
                alertType
                role
                severity
            }
            ... on InterfaceAlert {
                identity {
                    systemId
                    interface
                }
                expected {
                    obj
                }
                actual {
                    obj
                }
            }
            ... on RouteAlert {
                identity {
                    dstIp
                }
            }
        }
    }
    """)
    dump(results)
    return results
