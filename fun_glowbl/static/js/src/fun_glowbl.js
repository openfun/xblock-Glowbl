/* Javascript for FUNGlowblXBlock. */
function FUNGlowblXBlock(runtime, element) {
    $(function ($) {
        var $element = $(element);
        $element.find('.btn-lti-new-window').not('.is-studio').click(function(){
            // Add user privacy choices as querystring to next request
            var query = '';
            $element.find('input').each(function(idx, el) {
                query += el.value + '=' + el.checked + '&';
            })
            window.open($(this).data('target') + '?' + query);
        });
    });
}
