$(document).ready(function(){

  var assessment_id;
  var classification_id = 96;
  var listeners = [];
  var the_questions = [];
  
  setTokenAJAX();
  getClassifications();
  getQuestions(classification_id);

  // using jQuery
  function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
  }

  function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  }

  function setTokenAJAX() {
    var csrftoken = getCookie('csrftoken');
    
    $.ajaxSetup({
      beforeSend: function(xhr, settings) {
          if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
              xhr.setRequestHeader("X-CSRFToken", csrftoken);
          }
      }
    });
  }
  
  function getQuestions(category) {
    $.ajax({
      type: 'GET',
      url: '/api/question-category/' + category,
      success : function(responseClassification) {
        handleQuestions(responseClassification);
        assessment_id = $('input:hidden[name=assessment_id]').val();
      }
    });
  }

  function handleQuestions(questions) {
    var questions_container = $('.list-group')[0];
    questions_container.innerHTML = '';
    the_questions = questions;

    renderQuestions(questions, false, questions_container)
  }

  function renderQuestions(my_questions, hide, questions_container) {
    console.log('questions ', my_questions);
    
    for (var index = 0; index < my_questions.length; index++) {
      var element = my_questions[index];
      var answerId = element.answer ? element.answer.id : '';

      var li = $('<li/>')
                .addClass( "list-group-item question" )
                .attr( "id", element.id )
                .appendTo( questions_container );
      var p = $('<p/>')
              .text( element.id + ' - ' + element.text )
              .appendTo( li );
      var div = $('<div/>')
                .addClass( "btn-group question" )
                .attr( "role", "group" )
                .appendTo( li );
      var buttonYes = $('<button/>')
                      .text( "Yes" )
                      .addClass( "btn " + getBtnClass(true, element.answer))
                      .appendTo( div )
                      .attr( "data-question", element.id )
                      .attr( "data-value", "true" )
                      .attr( "data-answer-id", answerId )
                      .on( "click", handleAnswer );
      var buttonNo = $('<button/>')
                      .text( "No" )
                      .addClass( "btn " + getBtnClass(false, element.answer))
                      .attr( "data-question", element.id )
                      .attr( "data-value", "false" )
                      .attr( "data-answer-id", answerId )
                      .appendTo( div )
                      .on( "click", handleAnswer );
      
      hide ? li.hide() : li.show();

      if( element.children_yes ) {
        renderQuestions( element.children_yes, !element.answer ? true : !JSON.parse( element.answer.value ), questions_container );
      }
      if(element.children_no) {
        renderQuestions( element.children_no, !element.answer ? true : JSON.parse( element.answer.value ), questions_container );
      }
    }


    if( questions_container.innerHTML === '' ) {
      questions_container.innerHTML = 'No questions available';
    }
  }

  function getBtnClass( buttonVal, answer ) {
    if( buttonVal ) {
      return btn = !answer ? 'btn-default' : ( JSON.parse( answer.value ) && buttonVal ) ? 'btn-success' : 'btn-default';
    } else {
      return btn = !answer ? 'btn-default' :  JSON.parse( answer.value ) ? 'btn-default' : 'btn-success';        
    }
  }

  function handleAnswer() {
    var data = {
      "assessment": assessment_id,
      "question": $(this).attr("data-question"),
      "value": $(this).attr("data-value")
    };
    var answerId =  $(this).attr("data-answer-id");

    if(answerId) {
      updateAnswer(data, answerId);
    } else {
      saveAnswer(data);
    }
  }

  function getClassifications() {
    $.ajax({
      type: 'GET',
      url: '/api/classification',
      success : function(responseQuestions) {
        renderClassifications(responseQuestions);
        handleAccordion();
      }
    });
  }

  function renderClassifications(responseQuestions) {
    var accordion = $('#accordion')[0];
    accordion.innerHTML = '';

    for (var z = 0; z < responseQuestions.length; z++) {
      var element = responseQuestions[z];
      var h3 = $('<h3>').text(element.name).appendTo(accordion);
      var cList = $('<ul>');

      for (var j = 0; element.second_level && j < element.second_level.length; j++) {
        var subcat = element.second_level[j];
        var li = $('<li/>')
                  .text(subcat.name).attr("data-id", subcat.id)
                  .on( "click", getQuestionsForCat )
                  .appendTo(cList);
      }
      cList.appendTo(accordion);
    }
  }

  function handleAccordion() {
    $("#accordion").accordion({
      collapsible: true
    });
  }

  function saveAnswer(data) {

    $.ajax({
      "url": "/api/answers/",
      "type": "POST",
      "contentType": "application/json",
      "dataType": "json",
      "data": JSON.stringify(data),
    }).done(function (d) {

      updateQuestion(data, d);
      handleQuestions(the_questions);
    });
  }

  function updateAnswer(data, answerId) {

    $.ajax({
      "url": "/api/answers/" + answerId + "/",
      "type": "PUT",
      "contentType": "application/json",
      "dataType": "json",
      "data": JSON.stringify(data),
    }).done(function (d) {

        updateQuestion(data, d);
        handleQuestions(the_questions);
    });
  }

  function updateQuestion(data, d) {
     var modified_value = findNode(data.question.toString(), the_questions);

     modified_value.answer = {id: d.id, value: d.value};
  }

  function findNode(id, currentNode) {
    var i, result, elem, tempResult;

    if(!currentNode) {
      return;
    }

    for (i = 0; i < currentNode.length; i += 1) {
      elem = currentNode[i];
      
      if(elem.id.toString() === id) {
        result = elem;
        break;					
      } else {
        tempResult = findNode(id, elem.children_no);
        result = tempResult ? tempResult : result;
        
        if(!result) {
          tempResult = findNode(id, elem.children_yes);
          result = tempResult ? tempResult : result;
        }
      }
    }

    return result;
  }

  function getQuestionsForCat(val) {
    classification_id = $(this).attr("data-id");
    getQuestions(classification_id);
  }
});
 