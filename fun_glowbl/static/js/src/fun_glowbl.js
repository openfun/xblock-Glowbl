/* Javascript for FUNGlowblXBlock. */
function FUNGlowblXBlock(runtime, element) {
    $(function ($) {
        var $element = $(element);
        $element.find('.btn-lti-new-window').click(function(){
            window.open($(this).data('target'));
        });
    });
}
