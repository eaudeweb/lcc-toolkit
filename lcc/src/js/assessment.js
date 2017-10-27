/**
 * @module LegalAssessment
 * Handles the legal assesment
 */
$(document).ready(function(){
  'use strict'
  LCCTModules.define('LegalAssessment', ['Config', 'RequestService'], 
  function LegalAssessment(Config, RequestService){
      
    var assessment_id = $('input:hidden[name=assessment_id]').val();
    var user_id = $('input:hidden[name=user_id]').val();
    var classification_id = 15; // we only have data for this classification 
    var all_questions = [];
    var listeners = {};

    $( "#add-assessment" ).click(function() {
      RequestService
        .getCountries()
        .done(function (all_countries) {
          var country_list = $('#country-list');

          for (var j = 0; j < all_countries.length; j++) {
            var element = all_countries[j];
            var li_country = $('<option/>')
                              .text(element.name)
                              .attr('value', element.iso)
                              .appendTo(country_list);
          }
          $('#group-country-list').show();
          $('#country-list').change(handleCreateAssessment);
      });
    });

    $( "#continue-assessment" ).click(function() {
      RequestService
        .getAssessments()
        .done(function (all_assessments) {
          var country_list = $('#country-list');
          
          for (var j = 0; j < all_assessments.length; j++) {
            var element = all_assessments[j];
            var li_country = $('<option/>')
                              .text(element.country)
                              .attr('value', element.id)
                              .appendTo(country_list);
          }

          $('#group-country-list').show();

          // $('#assessment-landing').hide();
          // $('#assessment-edit').show();
          // getClassifications();
          $('#country-list').change(handleContinueAssessment);
      });
    });

    // $('#country-list').change(function () {
    //   var selected_country= $(this).find("option:selected").val();
    //   createAssessment(selected_country)
    // });
    
    function handleCreateAssessment() {
      var selected_country= $(this).find("option:selected").val();
      createAssessment(selected_country)
    }
    
    function handleContinueAssessment() {
      var selected_country= $(this).find("option:selected").val();
      continueAssessment(selected_country)
    }


    function createAssessment(country) {
      RequestService
      .createAssessment({country: country, user: user_id})
      .done(function (responseAssessment) {
        assessment_id = responseAssessment.id;
        $('#assessment-landing').hide();
        $('#assessment-edit').show();
        getClassifications(assessment_id);
      });
    }

    function continueAssessment(assessment_id) {
      assessment_id = assessment_id;
      $('#assessment-landing').hide();
      $('#assessment-edit').show();
      getClassifications(assessment_id);
    }




    function getClassifications(assessment_id) {
      RequestService
        .getClassifications(assessment_id)
        .done(function (responseClassifications) {

          renderClassifications(responseClassifications);
          handleAccordion();
          getQuestions(responseClassifications[0].second_level[0].id, assessment_id);
        });
    }
  
    function renderClassifications(responseQuestions) {
      var accordion = $('#accordion')[0];
      accordion.innerHTML = '';
  
      for (var z = 0; z < responseQuestions.length; z++) {
        var element = responseQuestions[z];
        var h3 = $('<h3>')
                  .text(element.name)
                  .appendTo(accordion);
        var classification_menu = $('<classification-menu/>')
                                  .addClass('flex lcct-list classification-menu')
                                  .attr('role', 'menu')
                                  .attr('tabindex', '0');

        for (var j = 0; element.second_level && j < element.second_level.length; j++) {
          var subcat = element.second_level[j];
          var classification_item = $('<classification-item/>')
                                    .addClass('toc-item lcct-list classification-item')
                                    .attr('role', 'option')
                                    .attr('tabindex', '0')
                                    .attr('aria-disabled', 'false')
                                    .attr('aria-selected', 'true')
                                    .attr('data-id', subcat.id)
                                    .on('click', getQuestionsForCategory)
                                    .appendTo(classification_menu);
          var i_comp = $('<i/>')
                        .text(j+1)
                        .addClass('lcct-list')
                        .appendTo(classification_item);
          var p = $('<span/>')
                    .text(subcat.name)
                    .addClass('lcct-list')
                    .appendTo(classification_item);
        }

        classification_menu.appendTo(accordion);
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
    
    function getQuestions(category, assessment_id) {
      RequestService
        .getQuestions(category, assessment_id)
        .done(function (responseClassification) {
          handleQuestions(responseClassification);
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
        createAnswer(data);
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
  
    function createAnswer(data) {
      RequestService
        .createAnswer(data)
        .done(function (responseAnswer) {

          listeners[data.question](data, responseAnswer);
          handleQuestions(all_questions);
        });
    }

    function getQuestionsForCategory(val) {
      var elem = $(this);
      var all_elems = $('classification-item').removeClass('iron-selected')
      elem.addClass('iron-selected');

      classification_id = elem.attr('data-id');
      getQuestions(classification_id, assessment_id);
    }
  });
});
