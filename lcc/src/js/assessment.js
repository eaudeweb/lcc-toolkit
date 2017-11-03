/**
 * @module LegalAssessment
 * Handles the legal assesment
 */
$(document).ready(function(){
  'use strict'
  LCCTModules.define('LegalAssessment', ['Config', 'RequestService'], 
  function LegalAssessment(Config, RequestService){
      
    this.assessment_id = null;
    var user_id = $('input:hidden[name=user_id]').val();
    var classification_id;
    var all_questions = [];
    var listeners = {};

    // TODO remove ids form questions

    // requests need the assessment_id, to have this available, we need to make sure
    // that functions have this as their context, which normally will be changed when:
    // - binding to $ elements
    // - calling inside promises from other modules
    renderCreateAssessment.call(this);
    renderContinueAssessment.call(this);
    renderQuestions.bind(this);
    renderViewResultsButton.call(this);

    function renderViewResultsButton() {
      var self = this;
      $('#assessment-results').click(function() {
        document.location.href = Config.url.assessment_results.replace('pk', self.assessment_id);
      });
    }

    function renderCreateAssessment() {
      var self = this;
      $('#add-assessment').click(function() {
        RequestService
          .getCountries()
          .done(function (all_countries) {
            var country_list = $('#country-list');
            country_list.empty();
            var li_country = $('<option/>')
                              .text('Select country')
                              .attr('value', '')
                              .appendTo(country_list);
                              
            for (var j = 0; j < all_countries.length; j++) {
              var element = all_countries[j];
              var li_country = $('<option/>')
                                .text(element.name)
                                .attr('value', element.iso)
                                .appendTo(country_list);
            }
            $('#group-country-list').show();
            $('#country-list').change(handleCreateAssessment.bind(self));
        });
      });
    }

    function renderContinueAssessment() {
      var self = this;
      $('#continue-assessment').click(function() {

        RequestService
          .getAssessments()
          .done(function (all_assessments) {
            var country_list = $('#country-list');
            country_list.empty();
            var li_country = $('<option/>')
                              .text('Select country')
                              .attr('value', '')
                              .appendTo(country_list);

            for (var j = 0; j < all_assessments.length; j++) {
              var element = all_assessments[j];
              var li_country = $('<option/>')
                                .text(element.country_name)
                                .attr('value', element.id)
                                .appendTo(country_list);
            }

            $('#group-country-list').show();
            $('#country-list').change(handleContinueAssessment.bind(self));
        });
      });
    }

    function handleCreateAssessment(event) {
      var selected_country= $(event.currentTarget).find('option:selected').val();
      createAssessment.call(this, selected_country)
    }

    function handleContinueAssessment(event) {
      this.assessment_id= $(event.currentTarget).find('option:selected').val();
      continueAssessment.call(this);
    }


    function createAssessment(country) {
      var self = this;
      RequestService
        .createAssessment({country: country, user: user_id})
        .done(function (responseAssessment) {
          self.assessment_id = responseAssessment.id;
          $('#assessment-landing').hide();
          $('#assessment-edit').show();
          getClassifications.call(self);
        });
    }

    function continueAssessment() {
      $('#assessment-landing').hide();
      $('#assessment-edit').show();
      getClassifications.call(this);
    }

    function getClassifications() {
      var self = this;
      RequestService
        .getClassifications(self.assessment_id)
        .done(function (responseClassifications) {

          renderClassifications.call(self, responseClassifications);
          handleAccordion();
          getQuestions.call(self, responseClassifications[0].second_level[0].id);
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
                                    .on('click', getQuestionsForCategory.bind(this))
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

    function getQuestions(classification_id) {
      var self = this;
      RequestService
        .getQuestions(classification_id, self.assessment_id)
        .done(function (responseQuestions) {
          handleQuestions.call(self, responseQuestions);
        });
    }

    function handleQuestions(questions) {
      var questions_container = $('.list-group')[0];
      questions_container.innerHTML = '';
      all_questions = questions;

      renderQuestions.call(this, questions, true, questions_container);
    }

    function renderQuestions(my_questions, show, questions_container, questionClass) {

      for (var index = 0; index < my_questions.length; index++) {
        var element = my_questions[index];
        var answerId = element.answer ? element.answer.id : '';
        questionClass = questionClass ? 'qq' + element.id : questionClass + '_' + element.id;
        var li = $('<li/>')
                  .addClass('list-group-item question' + questionClass)
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
                        .on('click', handleAnswer.bind(this, 
                          element.children_yes, element.children_no, 
                          true, questionClass + 'yes'));
                          
        var buttonNo = $('<button/>')
                        .text('No')
                        .addClass('btn ' + getBtnClass(false, element.answer))
                        .attr('data-question', element.id)
                        .attr('data-value', 'false')
                        .attr('data-answer-id', answerId)
                        .appendTo(div)
                        .on('click', handleAnswer.bind(this, 
                          element.children_yes, element.children_no, 
                          false, questionClass + 'no'));

        show ? li.show() : li.hide();

        if(element.children_yes) {
          renderQuestions.call(this
                                , element.children_yes
                                , show ? isShown(element, true) : show // will propagate false to all children
                                , questions_container
                                , questionClass + 'yes');
        }

        if(element.children_no) {
          renderQuestions.call(this
                                , element.children_no
                                , show ? isShown(element, false) : show
                                , questions_container
                                , questionClass + 'no');
        }  

        // through this closure each function has a reference to its question object,
        // updating it will be reflected in the collection of all_questions
        registerListeners(
          (function makeListener(element) {

            return function questionListener(d) {
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

    function isShown(element, buttonValue) {
      var response = false;
      if(!element.answer) {
        response = false;
      } else {
        response = element.answer.value ? buttonValue : !buttonValue; // this is a !XOR
      }

      return response;
    }

    // btn-success will suggest the existence of an answer
    // btn-default: no answer was given
    function getBtnClass(buttonVal, answer) {
      var btn;
      if(buttonVal) {
        return btn = !answer 
        ? 'btn-default' : (JSON.parse(answer.value) && buttonVal) 
        ? 'btn-success' : 'btn-default';
      } else {
        return btn = !answer 
        ? 'btn-default' :  JSON.parse(answer.value) 
        ? 'btn-default' : 'btn-success';        
      }
    }

    function handleAnswer(children_yes, children_no, isYesButton, questionClass, event) {
      var data = {
        'assessment': this.assessment_id,
        'question': $(event.currentTarget).attr('data-question'),
        'value': $(event.currentTarget).attr('data-value')
      };
      var answerId =  $(event.currentTarget).attr('data-answer-id');
      if(children_yes) {
        for (var index = 0; index < children_yes.length; index++) {
          var element = children_yes[index];
          if ( isYesButton ) {
            $(  "#" + element.id ).slideDown();
          } else {
            $(  "#" + element.id ).slideUp();
          }
        }
      }

      if(children_no) {
        for (var index = 0; index < children_no.length; index++) {
          var element = children_no[index];
          if ( isYesButton ) {
            $(  "#" + element.id ).slideUp();
          } else {
            $(  "#" + element.id ).slideDown();
          }
        }
      }
    
      if(answerId) {
        updateAnswer.call(this, data, answerId);
      } else {
        createAnswer.call(this, data);
      }
    }

    // instead of implementing a deep search function to find and update the answer/question
    // the listener will be called directly and update through reference the values of the answer
    function updateAnswer(data, answerId) {
      var self = this;
      RequestService
        .updateAnswer(data, answerId)
        .done(function (responseAnswer) {

          listeners[data.question](responseAnswer);
          handleQuestions.call(self, all_questions);
        });
    }

    function createAnswer(data) {
      var self = this;
      RequestService
        .createAnswer(data)
        .done(function (responseAnswer) {

          listeners[data.question](responseAnswer);
          handleQuestions.call(self, all_questions);
        });
    }

    function getQuestionsForCategory(event) {
      var elem = $(event.currentTarget);
      var all_elems = $('classification-item').removeClass('iron-selected')
      elem.addClass('iron-selected');

      classification_id = elem.attr('data-id');
      getQuestions.call(this, classification_id);
    }
  });
});
