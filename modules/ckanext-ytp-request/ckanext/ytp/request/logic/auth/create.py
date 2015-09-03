from ckanext.ytp.request.helper import get_user_member
import ckan.new_authz as authz
import logging
from ckan.common import _
log = logging.getLogger(__name__)

def member_request_create(context, data_dict):
    """ Create request access check """
    user = context.get('user',None)
    if not authz.auth_is_loggedin_user():
        return {'success': False, 'msg': _('User is not logged in')}

    organization_id = None if not data_dict else data_dict.get('organization_id', None)
    if organization_id:
        member = get_user_member(organization_id)
        if member:
            return {'success': False, 'msg': _('The user has already a pending request or an active membership')} 
    return {'success': True}

