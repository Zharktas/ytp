from ckan import model
from ckan.common import _, c
from sqlalchemy.sql.expression import or_
from ckanext.ytp.request.helper import get_user_member
import logging
log = logging.getLogger(__name__)

def member_request_membership_cancel(context, data_dict):
    if not c.userobj:
        return {'success': False}

    organization_id = data_dict.get("organization_id")
    if not organization_id:
        return {'success': False}

    member = get_user_member(organization_id, 'active')

    if not member:
        return {'success': False}

    if member.table_name == 'user' and member.table_id == c.userobj.id and member.state == u'active':
        return {'success': True}
    return {'success': False}


def member_request_cancel(context, data_dict):
    """ Cancel request access check.
        data_dict expects organization_id. See `logic.member_request_cancel`.
    """
    if not c.userobj:
        return {'success': False}

    organization_id = data_dict.get("organization_id")
    if not organization_id:
        return {'success': False}

    member = get_user_member(organization_id, 'pending')

    if not member:
        return {'success': False}

    if member.table_name == 'user' and member.table_id == c.userobj.id and member.state == u'pending':
        return {'success': True}
    return {'success': False}