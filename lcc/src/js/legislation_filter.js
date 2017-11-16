var payload = {'partial': true};

function activatePagination(){
  $("ul.pagination li a").on('click', function(){
    payload['page'] = $(this).attr('data-page');
    $(".submitBtn").click()
  });
}

$(document).ready(function(){

  var classifications = [];
  var countries = [];
  var law_types = [];
  var tags = [];

  activatePagination();

  // Activate multiselect
  $('#countrySelect').multipleSelect({
    width: '100%', multiple: true, multipleWidth: 260, filter: true
  });
  $('.ms-search').append(
    '<div class="search-icon">\
    <i class="fa fa-search" aria-hidden="true"></i>\
    </div>'
  );

  // Activate Slider
  $("#yearSlider").slider({formatter: function(value) {
		return value;
	}});

  $("#yearSlider").on("slide", function(slideEvt) {
    $("#fromYear").val(slideEvt.value[0]);
    $("#toYear").val(slideEvt.value[1]);
    payload['from_year'] = slideEvt.value[0];
    payload['to_year'] = slideEvt.value[1];
  });

  $('#textSearchInput').on('change', function() {
    payload['q'] = $(this).val();
  });

  $('#classificationsSelect input').on('change', function() {
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

  $('#countrySelect').on('change', function() {
    payload['countries'] = $(this).val();
  });

  $('#typeSelect input').on('change', function() {
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

  $('#tagSelect input').on('change', function() {
    if($(this).is(':checked')){
      if($.inArray($(this).val()) == -1){
        tags.push($(this).val())
      }
    }
    else {
      tags.splice(tags.indexOf($(this).val(), 1))
    }
    payload['tags'] = tags;
  });

  $(".submitBtn").on('click', function(){
    console.log(payload);
    $.ajax({
      type: 'GET',
      url: '/legislation',
      data: payload,
      success : function(data) {
        $("#laws").html(data);
        activatePagination();
      }
    });
  });
});
