$(document).ready(function(){
  var payload = {'partial': true};

  $('#textSearchInput').on('change', function() {
    payload['q'] = $(this).val();
  });

  $('#classificationsDropDown').on('change', function() {
    payload['classification'] = $(this).val();
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

  $('html').on('click', function(){
    // Clicking outside the classification dropdown closes it
    $("#classificationsDropDownWrapper").hide();
  })

  $('#classificationsDropDownWrapper').on('click', function(event){
    // Clicking inside the classification dropdown doesn't close it
    event.stopPropagation();
  })

  $("#classificationsDropDownToggler").on('click', function(event){
    // Toggle the dropdown on click
    event.stopPropagation();
    $("#classificationsDropDownWrapper").toggle();
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
