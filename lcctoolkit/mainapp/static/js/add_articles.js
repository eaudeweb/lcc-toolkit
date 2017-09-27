$(document).ready(function(){
  var AjaxSubmit = {}
  $max_page = parseInt($("#max_page").val());
  AjaxSubmit["law_id"] = $("#law_pk").val();


  $("#prev").on('click', function(){
    $page_number = parseInt($('#page_number').text()) - 2;
    AjaxSubmit["page_number"] = $page_number;
    $.ajax({
      type: 'GET',
      url: '/legislation/add/articles',
      data: AjaxSubmit,
      success : function(data) {
        $article_page = $(data).find('#raw-text-page');
        $page_number = $(data).find("#page_number");
        $("#raw-text-page").html('').append($article_page);
        $("#page_number").html('').append($page_number);
        $("#id_page").val(parseInt($page_number.text()));
      } 
    });
    // TODO verify this
    $("#next").prop("disabled", false);
    if( $page_number == 0) 
      $("#prev").prop("disabled", true);
    else
      $("#prev").prop("disabled", false);
  });

  $("#next").on('click', function(){
    $page_number = parseInt($('#page_number').text());
    AjaxSubmit["page_number"] = $page_number; 
    $.ajax({
      type: 'GET',
      url: '/legislation/add/articles',
      data: AjaxSubmit,
      success : function(data) {
        $article_page = $(data).find('#raw-text-page');
        $page_number = $(data).find("#page_number");
        $("#raw-text-page").html('').append($article_page);
        $("#page_number").html('').append($page_number);
        $("#id_page").val(parseInt($page_number.text()));
      } 
    });
    // TODO verify this
    $("#prev").prop("disabled", false);
    if( $page_number == $max_page) 
      $("#next").prop("disabled", true);
    else
      $("#next").prop("disabled", false);
  });

  console.log($("#law_pk").val());

  $("#save-and-continue-btn").on('click', function(){
    $page_number = parseInt($('#page_number').text());
    AjaxSubmit["page_number"] = $page_number;
    AjaxSubmit["code"] = $("#id_code").val();
    AjaxSubmit["legislation_text"] = $("#id_text").val();
    AjaxSubmit["page"] = $("#id_page").val();
    AjaxSubmit["csrfmiddlewaretoken"] = $("[name=csrfmiddlewaretoken]").val()
    AjaxSubmit["save-and-continue-btn"] = "";
    $('input:checkbox:checked').each(function(){
      AjaxSubmit[$(this).attr("name")] = 'on';
    });
    $.ajax({
      type: 'POST',
      url: '/legislation/add/articles',
      data: AjaxSubmit,
      success : function(data) {
        $article_form = $(data).find('#addArticle');
        $("#addArticle").html('').append($article_form);
      }
    });
  });


 });