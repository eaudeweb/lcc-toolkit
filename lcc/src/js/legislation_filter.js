var payload = {'partial': true};

function activatePagination(){
  $("ul.pagination li a").on('click', function(){
    payload['page'] = $(this).attr('data-page');
    $(".submitBtn").click()
  });
}

function send(payload){
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
}

$(document).ready(function(){

  var classifications = [];
  var countries = [];
  var law_types = [];
  var tags = [];

  var autocomplete = [];

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

  // Activate autocomplete

  $("#classificationsSelect > li.first-level > span > label").each(function(){
    autocomplete.push({
      id: $(this).attr('for'),
      name: $(this).html()
    });
  });

  $("#tagsSelect > li label").each(function(){
    autocomplete.push({
      id: $(this).attr('for'),
      name: $(this).html()
    });
  });

  $('#textSearchInput').easyAutocomplete({
    data: autocomplete,
    getValue: 'name',
    list: {
      maxNumberOfElements: 5,
  		match: {
  			enabled: true
  		},
      onChooseEvent: function() {
        var id = $("#textSearchInput").getSelectedItemData().id;
	      $("#" + id).click();
        $("#textSearchInput").val('').change();
  		}
  	}
  });
  $('div.easy-autocomplete').removeAttr('style');

  // Activate select/deselect links for classification filters

  $('a.select-all').on('click', function(){
    $(this).closest('ul').find('input').prop('checked', true);
  });

  $('a.deselect-all').on('click', function(){
    $(this).closest('ul').find('input').prop('checked', false);
  });

  // Handle search and filters

  $('#textSearchInput').on('change', function() {
    var val = $(this).val();
    if(val){
      payload['q'] = val;
    } else {
      delete payload['q'];
    }
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

  $('#tagsSelect input').on('change', function() {
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

  $('.submitBtn').on('click', function(){
    send(payload);
  });

  $('#textSearchInput').on('keyup', function(e){
    if(e.which == 13) {
      send(payload);
    }
  });

});
