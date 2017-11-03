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
    var classification_title = $('.classification_title');
    var current = $('#questions-container .current');
    var last = $('#questions-container .last');
    var question_category = $('.question_category')

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

      RequestService
        .getCountries()
        .done(function (all_countries) {
          var country_list = $('#country-list-new');
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
          handleCreateAssessment.call(self);
      });
    }

    function renderContinueAssessment() {
      var self = this;
      RequestService
        .getAssessments()
        .done(function (all_assessments) {
          var country_list = $('#country-list-continue');
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

          handleContinueAssessment.call(self);
      });
    }

    function handleCreateAssessment() {
      var self = this;
      $('#add-assessment').click(function(event) {
        var selected_country= $('#country-list-new').find('option:selected').val();
        createAssessment.call(self, selected_country)
      });
    }

    function handleContinueAssessment() {
      var self = this;
      $('#continue-assessment').click(function(event) {
        self.assessment_id= $('#country-list-continue').find('option:selected').val();
        continueAssessment.call(self);
      });
    }


    function createAssessment(country) {
      var self = this;
      RequestService
        .createAssessment({country: country, user: user_id})
        .done(function (responseAssessment) {
          self.assessment_id = responseAssessment.id;
          $('#assessment-landing').hide();
          $('#assessment-results-btn').show();
          $('#assessment-edit').show();
          getClassifications.call(self);
        });
    }

    function continueAssessment() {
      $('#assessment-landing').hide();
      $('#assessment-edit').show();
      $('#assessment-results-btn').show();
      getClassifications.call(this);
    }

    function getClassifications() {
      var self = this;
      RequestService
        .getClassifications(self.assessment_id)
        .done(function (responseClassifications) {

          renderClassifications.call(self, responseClassifications);
          handleAccordion();
          getQuestions.call(self, responseClassifications[0].second_level[0].id)
                      .done(renderTitleContent(responseClassifications[0].name
                                              , responseClassifications[0].second_level[0].name
                                              , responseClassifications[0].second_level.length
                                              , 0));
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
                                    .addClass('toc-item lcct-list classification-item' + (j == 0 && z == 0 ? ' iron-selected':''))
                                    .attr('role', 'option')
                                    .attr('tabindex', '0')
                                    .attr('aria-disabled', 'false')
                                    .attr('aria-selected', 'true')
                                    .attr('data-id', subcat.id)
                                    .on('click', getQuestionsForCategory.bind(this, element.name, subcat.name, element.second_level.length, j))
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
      var defer = $.Deferred();
      RequestService
        .getQuestions(classification_id, self.assessment_id)
        .done(function (responseQuestions) {
          handleQuestions.call(self, responseQuestions);
          defer.resolve();
        });
        return defer.promise();
    }

    function handleQuestions(questions) {
      var questions_container = $('.list-group')[0];
      questions_container.innerHTML = '';
      all_questions = questions;

      renderQuestions.call(this, questions, true, questions_container);
    }

    function renderQuestions(my_questions, show, questions_container, questionClass) {

      for (var index = 0; index < my_questions.length; index++) {
        var question = my_questions[index];
        var answerId = question.answer ? question.answer.id : '';
        questionClass = questionClass ? 'qq' + question.id : questionClass + '_' + question.id;
        var li = $('<li/>')
                  .addClass('list-group-item question' + questionClass)
                  .attr('id', question.id)
                  .appendTo(questions_container);
        var p = $('<p/>')
                .text(question.text)
                .appendTo(li);
        var div = $('<div/>')
                  .addClass('btn-group question')
                  .attr('role', 'group')
                  .appendTo(li);

        if(!question.children) {
          var buttonYes = $('<button/>')
                          .text('Yes')
                          .addClass('btn ' + getBtnClass(true, question.answer))
                          .appendTo(div)
                          .attr('data-question', question.id)
                          .attr('data-value', 'true')
                          .attr('data-answer-id', answerId)
                          .on('click', handleAnswer.bind(this, 
                            question.children_yes, question.children_no, 
                            true, questionClass + 'yes'));
          
          var buttonNo = $('<button/>')
                        .text('No')
                        .addClass('btn ' + getBtnClass(false, question.answer))
                        .attr('data-question', question.id)
                        .attr('data-value', 'false')
                        .attr('data-answer-id', answerId)
                        .appendTo(div)
                        .on('click', handleAnswer.bind(this, 
                          question.children_yes, question.children_no, 
                          false, questionClass + 'no'));
        }

        show ? li.show() : li.hide();

        if(question.children_yes) {
          renderQuestions.call(this
                                , question.children_yes
                                , show ? isShown(question, true) : show // will propagate false to all children
                                , questions_container
                                , questionClass + 'yes');
        }

        if(question.children_no) {
          renderQuestions.call(this
                                , question.children_no
                                , show ? isShown(question, false) : show
                                , questions_container
                                , questionClass + 'no');
        }

        if(question.children) {
          renderQuestions.call(this
                                , question.children
                                , show ? isShown(question, false, true) : show
                                , questions_container
                                , questionClass + 'no');
        }  

        // through this closure each function has a reference to its question object,
        // updating it will be reflected in the collection of all_questions
        registerListeners(
          (function makeListener(question) {

            return function questionListener(d) {
              question.answer = { 
                id: d.id, 
                value: d.value
              };
            }
          })(question)
        , question.id);
      }

      if(questions_container.innerHTML === '') {
        questions_container.innerHTML = 'No questions available';
      }
    }

    function isShown(element, buttonValue, force_show) {
      var response = false;
      if(force_show) {
        response = true;
      } else {
        if(!element.answer) {
          response = false;
        } else {
          response = element.answer.value ? buttonValue : !buttonValue; // this is a !XOR
        }
      }

      return response;
    }

    // btn-primary will suggest the existence of an answer
    // btn-default: no answer was given
    function getBtnClass(buttonVal, answer) {
      var btn;
      if(buttonVal) {
        return btn = !answer 
        ? 'btn-default' : (JSON.parse(answer.value) && buttonVal) 
        ? 'btn-primary' : 'btn-default';
      } else {
        return btn = !answer 
        ? 'btn-default' :  JSON.parse(answer.value) 
        ? 'btn-default' : 'btn-primary';        
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
          if (isYesButton) {
            $('#' + element.id).slideDown();
          } else {
            $('#' + element.id).slideUp();
          }
        }
      }

      if(children_no) {
        for (var index = 0; index < children_no.length; index++) {
          var element = children_no[index];
          if (isYesButton) {
            $('#' + element.id).slideUp();
          } else {
            $('#' + element.id).slideDown();
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

    function getQuestionsForCategory(classification_name, category_name, categories_no, index, event) {
      var elem = $(event.currentTarget);
      var all_elems = $('classification-item').removeClass('iron-selected')
      elem.addClass('iron-selected');
      classification_id = elem.attr('data-id');
      getQuestions.call(this, classification_id);
      renderTitleContent(classification_name, category_name, categories_no, index);
      handleNextQuestions(false)
    }





    $('.next_question').click(handleNextQuestions.bind(this, true))


    function handleNextQuestions(shouldClick){

      var question_categories = $('.ui-accordion-content-active classification-item');
      var classifications = $('.ui-accordion-header')
      var selected_question_category_index;
      var selected_classifications_index;

      classifications.each(function(index,item){
        if($(item).hasClass('ui-accordion-header-active')){
          selected_classifications_index = index;
        }
      })

      question_categories.each(function(index,item){
        if($(item).hasClass('iron-selected')){
          selected_question_category_index = index
        }
      })

        var next_category = question_categories[selected_question_category_index + 1];
        var click_nextext = question_categories[selected_question_category_index + 2];
        if(shouldClick == false){
          click_nextext = next_category
        }
      if(selected_question_category_index < question_categories.length - 1){
        if(shouldClick == true){
          next_category.click();
        }
        next_category = question_categories[selected_question_category_index + 1];
        var text = $(click_nextext).find('span').text();
        $('.next_category').html(text)
      }
      else {
        var title = classifications[selected_classifications_index + 1]
        var controls = $(title).attr('aria-controls'); 

        // TODO remove button for last question
        try{
          if(shouldClick == true){
            title.click();
            $('classification-menu#'+controls+'').find('classification-item:first-of-type').click();
          }
        }catch(e){
          
        }
        // $('.next_question').remove();
      }
    }

    function renderTitleContent(classification_name, category_name, categories_no, index) {
      classification_title.html(classification_name);
      current.html(parseInt(index) + 1);
      last.html(categories_no);
      question_category.html(category_name);
    }
  });
});
