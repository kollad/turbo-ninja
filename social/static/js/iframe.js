function start_iframe(swf_url, data) {
    var flashvars = data['flashvars'];
    var params = {
        wmode: data['settings']['swf']['wmode'],
        allowFullScreen: true
    };
    var attributes = {};
    swfobject.embedSWF(
        swf_url,
        "game",
        data['settings']['swf']['width'],
        data['settings']['swf']['height'],
        "10.0.0", false, flashvars, params, attributes
    );
}