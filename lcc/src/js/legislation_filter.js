$(document).ready(function(){
  var AjaxSubmit = {}

  $('#TagDropDown').on('change',function(e){
    AjaxSubmit['tags'] = $(this).val();
  });

  $('#classificationsDropDown').on('change', function() {
    AjaxSubmit['classification'] = $(this).val();
  });

  $('#countriesDropDown').on('click', function() {
    AjaxSubmit['country'] = $('#countriesDropDown option:selected').val();
  });

  $('#typeDropDown').on('click', function() {
    AjaxSubmit['type'] = $('#typeDropDown option:selected').val();
  });

  $("#submitButton").on('click', function(){
    console.log(AjaxSubmit)
    $.ajax({
      type: 'GET',
      url: '/legislation',
      data: AjaxSubmit,
      success : function(data) {
        $laws = $(data).find('#laws');
        $laws_container = $laws.find('.law-container').html()
        $("#laws").html('').append($laws_container)
        if($laws_container.length == 0) {
          $('#laws').html('<span class="error">No legislation found</span>')
        }
      }
    });
  });

 });
