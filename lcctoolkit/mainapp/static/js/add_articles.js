$(document).ready(function(){
  var AjaxSubmit = {}
  $max_page = parseInt($("#page_number").attr("max_page"));

  $("#prev").on('click', function(){
    $page_number = parseInt($('#page_number').text()) - 2;
    AjaxSubmit["page_number"] = $page_number;
    AjaxSubmit["law_id"] = $("#title").attr("pk");
    console.log(AjaxSubmit)
    $.ajax({
      type: 'GET',
      url: '/legislation/add/articles',
      data: AjaxSubmit,
      success : function(data) {
        $article_page = $(data).find('#raw-text-page');
        $page_number = $(data).find("#page_number");
        $("#raw-text-page").html('').append($article_page)
        $("#page_number").html('').append($page_number)
      } 
    });
    $("#next").prop("disabled", false);
    if( $page_number == 0) 
      $("#prev").prop("disabled", true);
    else
      $("#prev").prop("disabled", false);
  });


  $("#next").on('click', function(){
    $page_number = parseInt($('#page_number').text());
    AjaxSubmit["page_number"] = $page_number; 
    AjaxSubmit["law_id"] = $("#title").attr("pk");
    console.log(AjaxSubmit)
    $.ajax({
      type: 'GET',
      url: '/legislation/add/articles',
      data: AjaxSubmit,
      success : function(data) {
        $article_page = $(data).find('#raw-text-page');
        $page_number = $(data).find("#page_number");
        $("#raw-text-page").html('').append($article_page)
        $("#page_number").html('').append($page_number)
      } 
    });
    $("#prev").prop("disabled", false);
    if( $page_number == $max_page) 
      $("#next").prop("disabled", true);
    else
      $("#next").prop("disabled", false);
  })


 });