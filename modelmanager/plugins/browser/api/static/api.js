function call_function(callurl, result_element) {
  var result_elem = django.jQuery(result_element);
  result_elem.html('<h5>Thinking...</h5>');
  django.jQuery.ajax({
    url:  callurl,
    async: true,
    success: function(d) {result_elem.html(d);},
    error: function (e) {
      console.log(e);
      result_elem.html('<h5>Something went wrong.</h5>');
      }
    });
};
