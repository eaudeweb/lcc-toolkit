function changePage(item, page_number) {
    var pdf_page = item.attr('data').replace(/#page=\d+/, '#page='+page_number)
    item.attr("data", pdf_page);
}

$(document).ready(function(){

  var AjaxSubmit = {};
  AjaxSubmit["law_id"] = $("#law_pk").val();
  var page_number = parseInt($("#page_number").text());
  var pages = null;

  $.ajax({
    dataType: "json",
    url: '/legislation/pages',
    async: false,
    data: {'law_id': AjaxSubmit["law_id"]},
    success: function(data) {
      pages = data;
    }
  });

  $max_page = Object.keys(pages).length;
  document.getElementById("raw-text-page").innerHTML = pages[$("#starting_page").val()];

  $("#prev").on('click', function(){
    page_number = page_number - 1;
    document.getElementById("raw-text-page").innerHTML = pages[page_number];
    document.getElementById("page_number").innerHTML = page_number;
    document.getElementById("id_page").value = page_number;
    // TODO verify this
    changePage($('.pdf'), page_number)
    $("#next").prop("disabled", false);
    if( page_number == 1)
      $("#prev").prop("disabled", true);
    else
      $("#prev").prop("disabled", false);
  });

  $("#next").on('click', function(){
    page_number = page_number + 1;
    document.getElementById("raw-text-page").innerHTML = pages[page_number];
    document.getElementById("page_number").innerHTML = page_number;
    document.getElementById("id_page").value = page_number;
    changePage($('.pdf'), page_number)
    $("#prev").prop("disabled", false);
    if( page_number == $max_page)
      $("#next").prop("disabled", true);
    else
      $("#next").prop("disabled", false);
  });

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
