$(document).ready(function(){
  var payload = {'partial': true};
  var classifications = [];
  var law_types = [];

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
    payload['classifications'] = classifications;
  });

  $('#TagDropDown').on('change',function(e){
    payload['tags'] = $(this).val();
  });

  $('#countryDropDown').on('change', function() {
    payload['country'] = $('#countryDropDown option:selected').val();
  });

  $('#typeDropDown input').on('change', function() {
    if($(this).is(':checked')){
      if($.inArray($(this).val()) == -1){
        law_types.push($(this).val())
      }
    }
    else {
      law_types.splice(law_types.indexOf($(this).val(), 1))
    }
    payload['law_types'] = law_types;
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
