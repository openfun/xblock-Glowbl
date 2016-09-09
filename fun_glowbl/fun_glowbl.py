# -*- coding: utf-8 -*-

import pkg_resources

from django.conf import settings

from xblock.core import String, Scope, XBlock
from xblock.fragment import Fragment
from xblockutils.resources import ResourceLoader
from xblockutils.studio_editable import StudioEditableXBlockMixin

from lti_consumer import LtiConsumerXBlock


def _(text):
    return text

# if no settings, ltiapps.net/test/tp.php is a LTI development tool
GLOWBL_LTI_ENDPOINT = getattr(settings, 'GLOWBL_LTI_ENDPOINT', 'http://ltiapps.net/test/tp.php')
GLOWBL_LTI_KEY = getattr(settings, 'GLOWBL_LTI_KEY', 'jisc.ac.uk')
GLOWBL_LTI_SECRET = getattr(settings, 'GLOWBL_LTI_SECRET', 'secret')
GLOWBL_LTI_ID = getattr(settings, 'GLOWBL_LTI_ID', 'testtoolconsumer')
GLOWBL_LAUNCH_URL = getattr(settings, 'GLOWBL_LAUNCH_URL', 'http://ltiapps.net/test/tp.php')

BUTTON_TEXT = _("Click here !")

# FUNGlowblXBlock is a wrapper around edX LTI consumer xblock (which must be installed)
# to ease configuration for Glowbl service


@XBlock.needs('i18n')
class FUNGlowblXBlock(LtiConsumerXBlock, StudioEditableXBlockMixin, XBlock):

    editable_fields = ['title', 'description', 'rendezvous']

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

    def __init__(self, *args, **kwargs):
        super(FUNGlowblXBlock, self).__init__(*args, **kwargs)
        self.lti_id = GLOWBL_LTI_ID
        self.lti_key = GLOWBL_LTI_KEY
        self.lti_secret = GLOWBL_LTI_SECRET
        self.launch_url = GLOWBL_LTI_ENDPOINT
        self.custom_parameters = []

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

        logo = self.runtime.local_resource_url(self, 'static/img/logo-glowbl.png')
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

            'element_id': self.location.html_id(),  # pylint: disable=no-member
            'element_class': '',
            'title': self.title,
            'description': self.description,
            'rendezvous': self.rendezvous,
            'form_url': self.runtime.handler_url(self, 'lti_launch_handler').rstrip('/?'),
            'button_text': BUTTON_TEXT,
            'launch_url': GLOWBL_LAUNCH_URL,
        }



    # TO-DO: change this to create the scenarios you'd like to see in the
    # workbench while developing your XBlock.
    @staticmethod
    def workbench_scenarios():
        """A canned scenario for display in the workbench."""
        return [
            ("FUNGlowblXBlock",
             """<fun_glowbl/>
             """),
            ("Multiple FUNGlowblXBlock",
             """<vertical_demo>
                <fun_glowbl/>
                <fun_glowbl/>
                <fun_glowbl/>
                </vertical_demo>
             """),
        ]
