$(document).ready(function(){
  var payload = {'partial': true};
  var classifications = [];

  $('#textSearchInput').on('change', function() {
    payload['q'] = $(this).val();
  });

  $('#classificationsDropDown input').on('change', function() {
    if($(this).is(':checked')){
      if($.inArray($(this).val()) == -1){
        classifications.push($(this).val())
      }
    }
    else {
      classifications.splice(classifications.indexOf($(this).val(), 1))
    }
    payload['classification'] = classifications;
  });

  $('#TagDropDown').on('change',function(e){
    payload['tags'] = $(this).val();
  });

  $('#countryDropDown').on('change', function() {
    payload['country'] = $('#countryDropDown option:selected').val();
  });

  $('#typeDropDown').on('change', function() {
    payload['type'] = $('#typeDropDown option:selected').val();
  });


  $(".submitBtn").on('click', function(){
    console.log(payload);
    $.ajax({
      type: 'GET',
      url: '/legislation',
      data: payload,
      success : function(data) {
        $("#laws").html(data);
      }
    });
  });
});
