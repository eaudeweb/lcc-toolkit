/**
 * @module LegalAssessment
 * Handles the legal assesment
 */
$(document).ready(function(){
  'use strict'
  LCCTModules.define('LegalAssessment', ['Config', 'RequestService'], 
  function LegalAssessment(Config, RequestService){
      
    var assessment_id;
    var classification_id = 96;
    var all_questions = [];
    var listeners = {};

    getClassifications();
    getQuestions(classification_id);
      
    function getClassifications() {
      RequestService
        .getClassifications()
        .done(function (responseQuestions) {

          renderClassifications(responseQuestions);
          handleAccordion();
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
                    .text(subcat.name).attr('data-id', subcat.id)
                    .on('click', getQuestionsForCategory)
                    .appendTo(cList);
        }
        cList.appendTo(accordion);
      }
    }
  
    function handleAccordion() {
      $('#accordion').accordion({
        collapsible: true
      });
    }

    function registerListeners(handler, id) {
      listeners[id] = handler;
    }
    
    function getQuestions(category) {
      RequestService
        .getQuestions(category)
        .done(function (responseClassification) {

          handleQuestions(responseClassification);
          assessment_id = $('input:hidden[name=assessment_id]').val();
        });
    }
  
    function handleQuestions(questions) {
      var questions_container = $('.list-group')[0];
      questions_container.innerHTML = '';
      all_questions = questions;
  
      renderQuestions(questions, false, questions_container)
    }
  
    function renderQuestions(my_questions, hide, questions_container) {
      
      for (var index = 0; index < my_questions.length; index++) {
        var element = my_questions[index];
        var answerId = element.answer ? element.answer.id : '';
  
        var li = $('<li/>')
                  .addClass('list-group-item question')
                  .attr('id', element.id)
                  .appendTo(questions_container);
        var p = $('<p/>')
                .text(element.id + ' - ' + element.text)
                .appendTo(li);
        var div = $('<div/>')
                  .addClass('btn-group question')
                  .attr('role', 'group')
                  .appendTo(li);
        var buttonYes = $('<button/>')
                        .text('Yes')
                        .addClass('btn ' + getBtnClass(true, element.answer))
                        .appendTo(div)
                        .attr('data-question', element.id)
                        .attr('data-value', 'true')
                        .attr('data-answer-id', answerId)
                        .on('click', handleAnswer);
        var buttonNo = $('<button/>')
                        .text('No')
                        .addClass('btn ' + getBtnClass(false, element.answer))
                        .attr('data-question', element.id)
                        .attr('data-value', 'false')
                        .attr('data-answer-id', answerId)
                        .appendTo(div)
                        .on('click', handleAnswer);
        
        hide ? li.hide() : li.show();
  
        if(element.children_yes) {
          renderQuestions(element.children_yes, !element.answer ? true : !JSON.parse(element.answer.value), questions_container);
        }

        if(element.children_no) {
          renderQuestions(element.children_no, !element.answer ? true : JSON.parse(element.answer.value), questions_container);
        }  

        registerListeners(
          (function makeListener(element) {

            return function questionListener(data, d) {
              element.answer = { 
                id: d.id, 
                value: d.value
              };
            }
          })(element)
        , element.id);
      }
  
      if(questions_container.innerHTML === '') {
        questions_container.innerHTML = 'No questions available';
      }
    }
  
    function getBtnClass(buttonVal, answer) {
      var btn;
      if(buttonVal) {
        return btn = !answer ? 'btn-default' : (JSON.parse(answer.value) && buttonVal) ? 'btn-success' : 'btn-default';
      } else {
        return btn = !answer ? 'btn-default' :  JSON.parse(answer.value) ? 'btn-default' : 'btn-success';        
      }
    }
  
    function handleAnswer() {
      var data = {
        'assessment': assessment_id,
        'question': $(this).attr('data-question'),
        'value': $(this).attr('data-value')
      };
      var answerId =  $(this).attr('data-answer-id');
  
      if(answerId) {
        updateAnswer(data, answerId);
      } else {
        saveAnswer(data);
      }
    }
  
    function updateAnswer(data, answerId) {
      RequestService
        .updateAnswer(data, answerId)
        .done(function (responseAnswer) {

          listeners[data.question](data, responseAnswer);
          handleQuestions(all_questions);
        });
    }
  
    function saveAnswer(data) {
      RequestService
        .saveAnswer(data)
        .done(function (responseAnswer) {

          listeners[data.question](data, responseAnswer);
          handleQuestions(all_questions);
        });
    }

    function getQuestionsForCategory(val) {
      classification_id = $(this).attr('data-id');
      getQuestions(classification_id);
    }
  });
});
