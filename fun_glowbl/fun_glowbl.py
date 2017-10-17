# -*- coding: utf-8 -*-

import pkg_resources
from webob import Response
from pprint import pprint
import urllib

from django.conf import settings

from openedx.core.djangoapps.user_api.accounts.image_helpers import get_profile_image_names

from xblock.core import String, Scope, XBlock
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

from lti_consumer import LtiConsumerXBlock
from lti_consumer.oauth import get_oauth_request_signature
from lti_consumer.lti import LtiConsumer

def _(text):
    return text

# if no settings, ltiapps.net/test/tp.php is a LTI development tool
GLOWBL_LTI_ENDPOINT = getattr(settings, 'GLOWBL_LTI_ENDPOINT', 'http://ltiapps.net/test/tp.php')
GLOWBL_LTI_KEY = getattr(settings, 'GLOWBL_LTI_KEY', 'jisc.ac.uk')
GLOWBL_LTI_SECRET = getattr(settings, 'GLOWBL_LTI_SECRET', 'secret')
GLOWBL_LTI_ID = getattr(settings, 'GLOWBL_LTI_ID', 'testtoolconsumer')
GLOWBL_LAUNCH_URL = getattr(settings, 'GLOWBL_LAUNCH_URL', 'http://ltiapps.net/test/tp.php')
GLOWBL_COLL_OPT = "FunMoocJdR"

BUTTON_TEXT = _(u"Accéder à la conférence Glowbl et accepter la transmission de mon nom d'utilisateur et de mon avatar")


# inherit LtiConsumer for better user private information granularity
class FUNLtiConsumer(LtiConsumer):

    def get_signed_lti_parameters(self):
        """
        Signs LTI launch request and returns signature and OAuth parameters.
        Arguments:
            None
        Returns:
            dict: LTI launch parameters
        """
        # Must have parameters for correct signing from LTI:
        lti_parameters = {
            u'user_id': self.xblock.user_id,
            u'oauth_callback': u'about:blank',
            u'launch_presentation_return_url': '',
            u'lti_message_type': u'basic-lti-launch-request',
            u'lti_version': 'LTI-1p0',
            u'roles': self.xblock.role,

            # Parameters required for grading:
            u'resource_link_id': self.xblock.resource_link_id,
            u'lis_result_sourcedid': self.xblock.lis_result_sourcedid,

            u'context_id': self.xblock.context_id,
            u'custom_component_display_name': self.xblock.display_name,
        }

        if self.xblock.due:
            lti_parameters['custom_component_due_date'] = self.xblock.due.strftime('%Y-%m-%d %H:%M:%S')
            if self.xblock.graceperiod:
                lti_parameters['custom_component_graceperiod'] = str(self.xblock.graceperiod.total_seconds())

        if self.xblock.has_score:
            lti_parameters.update({
                u'lis_outcome_service_url': self.xblock.outcome_service_url
            })

        # Username, email, and language can't be sent in studio mode, because the user object is not defined.
        # To test functionality test in LMS
        if callable(self.xblock.runtime.get_real_user):
            real_user_object = self.xblock.runtime.get_real_user(self.xblock.runtime.anonymous_student_id)

            lti_parameters["lis_person_sourcedid"] = real_user_object.username if self.xblock.send_username else 'private'
            user_firstname = real_user_object.first_name if self.xblock.send_firstname else 'private'
            user_lastname = real_user_object.last_name if self.xblock.send_lastname else 'private'
            lti_parameters["lis_person_name_full"] = user_firstname + ' ' + user_lastname

            lti_parameters["lis_person_contact_email_primary"] = real_user_object.email if self.xblock.send_email else 'private'

            # Appending custom parameter for signing.
            lti_parameters.update(self.xblock.prefixed_custom_parameters)

        headers = {
            # This is needed for body encoding:
            'Content-Type': 'application/x-www-form-urlencoded',
        }

        key, secret = self.xblock.lti_provider_key_secret
        oauth_signature = get_oauth_request_signature(key, secret, self.xblock.launch_url, headers, lti_parameters)

        # Parse headers to pass to template as part of context:
        oauth_signature = dict([param.strip().replace('"', '').split('=') for param in oauth_signature.split(',')])

        oauth_signature[u'oauth_nonce'] = oauth_signature.pop(u'OAuth oauth_nonce')

        # oauthlib encodes signature with
        # 'Content-Type': 'application/x-www-form-urlencoded'
        # so '='' becomes '%3D'.
        # We send form via browser, so browser will encode it again,
        # So we need to decode signature back:
        oauth_signature[u'oauth_signature'] = urllib.unquote(oauth_signature[u'oauth_signature']).decode('utf8')

        # Add LTI parameters to OAuth parameters for sending in form.
        lti_parameters.update(oauth_signature)
        return lti_parameters


# FUNGlowblXBlock is a wrapper around edX LTI consumer xblock (which must be installed)
# to ease configuration for Glowbl service

@XBlock.needs('i18n')
class FUNGlowblXBlock(LtiConsumerXBlock, StudioEditableXBlockMixin, XBlock):

    editable_fields = ['title', 'description', 'rendezvous', 'custom_course_type', 'max_user']

    display_name = String(scope=Scope.settings, default=_("FUN Glowbl"),
        display_name=_("Display Name"))

    title = String(scope=Scope.settings, default="",
        display_name=_("Glowbl Live Event title"),
        help=_("Enter the title of the event."))

    description = String(scope=Scope.settings, default="",
        display_name=_("Glowbl Live Event description"),
        help=_("Enter a description of the event."))

    rendezvous = String(scope=Scope.settings, default="",
        display_name=_("Glowbl Live Event date"),
        help=_("Enter date and hour of the event."))

    custom_course_type = String(scope=Scope.settings, default="0",
        display_name=_("Custom course type"),
        help=_('Define the type of the course. Let to default "0" for a normal course. Set to "1" for small groups and role play game'))

    max_user = String(scope=Scope.settings, default="",
        display_name=_("Maximum of user"),
        help=_("Maximum of user for the class. It is an optional field"))


    def __init__(self, *args, **kwargs):
        super(FUNGlowblXBlock, self).__init__(*args, **kwargs)
        self.lti_id             = GLOWBL_LTI_ID
        self.lti_key            = GLOWBL_LTI_KEY
        self.lti_secret         = GLOWBL_LTI_SECRET
        self.launch_url         = GLOWBL_LTI_ENDPOINT
        self.custom_parameters  = []
        self.send_email         = False
        self.send_username      = True
        self.send_firstname     = True
        self.send_profile_image = True
        self.send_lastname      = False

    def _is_studio(self):
        studio = False
        try:
            studio = self.runtime.is_author_mode
        except AttributeError:
            pass
        return studio

    def _user_is_staff(self):
        return getattr(self.runtime, 'user_is_staff', False)

    def get_icon_class(self):
        """Return the CSS class to be used in courseware sequence list."""
        return 'seq_other'

    def resource_string(self, path):
        """Handy helper for getting resources from our kit."""
        data = pkg_resources.resource_string(__name__, path)
        return data.decode("utf8")

    def student_view(self, context=None):
        """
        The primary view of the FUNGlowblXBlock, shown to students
        when viewing courses.
        """
        fragment = Fragment()
        loader = ResourceLoader(__name__)
        context.update(self._get_context_for_template())

        logo = self.runtime.local_resource_url(self, 'public/img/logo-glowbl.png')
        context.update({'logo': logo})

        fragment.add_content(loader.render_mako_template('static/html/fun_glowbl.html', context))
        fragment.add_css(loader.load_unicode('static/css/fun_glowbl.css'))
        fragment.add_javascript(self.resource_string("static/js/src/fun_glowbl.js"))
        fragment.initialize_js('FUNGlowblXBlock')
        return fragment

    @property
    def lti_provider_key_secret(self):
        return self.lti_key, self.lti_secret

    def _get_context_for_template(self):
            return {
                'is_studio': 'is-studio' if (
                    self._is_studio())  else '',
                'element_id': self.location.html_id(),  # pylint: disable=no-member
                'element_class': '',
                'title': self.title,
                'description': self.description,
                'rendezvous': self.rendezvous,
                'custom_course_type': self.custom_course_type,
                'max_user':self.max_user,
                'form_url': self.runtime.handler_url(self, 'lti_launch_handler').rstrip('/?'),
                'button_text': BUTTON_TEXT,
                'launch_url': GLOWBL_LAUNCH_URL,
            }

    @XBlock.handler
    def lti_launch_handler(self, request, suffix=''):  # pylint: disable=unused-argument
        """
        XBlock handler for launching the LTI provider.

        Displays a form which is submitted via Javascript
        to send the LTI launch POST request to the LTI
        provider.

        Arguments:
            request (xblock.django.request.DjangoWebobRequest): Request object for current HTTP request
            suffix (unicode): Request path after "lti_launch_handler/"

        Returns:
            webob.response: HTML LTI launch form
        """

        self.lti_consumer = FUNLtiConsumer(self)
        self.lti_parameters = self.lti_consumer.get_signed_lti_parameters()
        pprint(self.lti_parameters)
        loader = ResourceLoader(__name__)
        context = self._get_context_for_template()
        context.update({'lti_parameters': self.lti_parameters})
        template = loader.render_mako_template('static/html/lti_launch.html', context)
        return Response(template, content_type='text/html')

    @property
    def prefixed_custom_parameters(self):
        """
        This function is called by LtiConsumer to add custom values to lti parameters
        We add profile image and xblock fields.
        """
        custom_parameters = {
            'custom_title': self.title,
            'custom_description': self.description,
            'custom_rendezvous': self.rendezvous,
            'custom_max_user': self.max_user,
        }
        # user fat finger prevention comparing on lower stripped strings
        if self.custom_course_type.strip().lower() == "1":
            custom_parameters['custom_course_type'] = GLOWBL_COLL_OPT
            valid_number_of_user = self.max_user.strip().isdigit()
            if valid_number_of_user:
                custom_parameters['custom_max_user'] = int(self.max_user)

        if callable(self.runtime.get_real_user):
            real_user_object = self.runtime.get_real_user(self.runtime.anonymous_student_id)
            username = real_user_object.username if self.send_username else 'private'
            first_name = real_user_object.first_name if self.send_username else 'private'
            images = get_profile_image_names(username) if self.send_profile_image else 'private'
            custom_parameters['custom_profile_image_url'] = 'https://fun-mooc.fr/media/profile-images/%s' % images[50]
        return custom_parameters
