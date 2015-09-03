from ckan import model, logic
from ckan.plugins import toolkit
from sqlalchemy.sql.expression import or_
from ckan.lib.dictization import model_dictize
from ckan.logic import NotFound, ValidationError, check_access
from ckan.common import _, c
from ckan.lib import helpers
from pylons import config
from ckanext.ytp.request.model import MemberRequest
from ckan.lib.helpers import url_for
from ckanext.ytp.request.mail import mail_new_membership_request
from ckanext.ytp.request.helper import get_safe_locale
import logging
import ckan.new_authz as authz

log = logging.getLogger(__name__)

def member_request_create(context, data_dict):
    ''' Create new member request. User is taken from context. 
    Sysadmins should not be able to create "member" requests since they have full access to all organizations
    :param group: name of the group or organization
    :type group: string
    '''
    logic.check_access('member_request_create', context, data_dict)
    member = _create_member_request(context, data_dict)
    return model_dictize.member_dictize(member, context)
    
def _create_member_request(context, data_dict):
    """ Helper to create member request """
    role = data_dict['role']
    group = model.Group.get(data_dict['group'])

    if not group or group.type != 'organization':
        raise NotFound

    user = context.get('user',None)

    if authz.is_sysadmin(user):
        raise ValidationError({}, {_("Role"): _("As a sysadmin, you already have access to all organizations")})

    userobj = model.User.get(user)

    member = model.Session.query(model.Member).filter(model.Member.table_name == "user").filter(model.Member.table_id == userobj.id) \
        .filter(model.Member.group_id == group.id).first()

    ## If there is a member for this organization...
    if member:
        if member.state == 'pending':
            message = _("You already have a pending request to the organization")
        elif member.state == 'active':
            message = _("You are already part of the organization")
        #Should never happen
        else:
            message = _("Existing member with unknown status")
        raise ValidationError({"organization": _("Duplicate organization request")}, {_("Organization"): message})

    else:
        member = model.Member(table_name="user", table_id=userobj.id, group_id=group.id, capacity=role, state='pending')

    locale = get_safe_locale()

    member.state = 'pending'
    member.capacity = role
    revision = model.repo.new_revision()
    revision.author = user
    revision.message = u'New member request'
    model.Session.add(member)

    memberRequest = MemberRequest(member_id=member.id, language=locale, organization_id=group.id)
    model.Session.add(memberRequest)
    model.repo.commit()

    if role == 'admin':
        for admin in _get_ckan_admins():
            mail_new_membership_request(locale, admin, group.display_name, "", userobj.display_name, userobj.email)
    else:
        for admin in _get_organization_admins(group.id):
            mail_new_membership_request(locale, admin, group.display_name, "", userobj.display_name, userobj.email)

    return member

def _get_organization_admins(group_id):
    admins = set(model.Session.query(model.User).join(model.Member, model.User.id == model.Member.table_id).
                 filter(model.Member.table_name == "user").filter(model.Member.group_id == group_id).
                 filter(model.Member.state == 'active').filter(model.Member.capacity == 'admin'))

    admins.update(set(model.Session.query(model.User).filter(model.User.sysadmin == True)))  # noqa

    return admins


def _get_ckan_admins():
    admins = set(model.Session.query(model.User).filter(model.User.sysadmin == True))  # noqa

    return admins
