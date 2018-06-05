/**
 * @module LegalAssessment
 * Handles the legal assesment
 */
$(document).ready(function () {
  'use strict'
  LCCTModules.define('LegalAssessment', ['Config', 'RequestService'],
    function LegalAssessment(Config, RequestService) {

      this.assessment_id = null;
      var user_id = $('input:hidden[name=user_id]').val();
      var classification_id;
      var all_questions = [];
      var listeners = {};
      var classification_title = $('.classification_title');
      var current = $('#questions-container .current');
      var last = $('#questions-container .last');
      var question_category = $('.question_category');
      var continue_countries = [];

      var href_content = window.location.href.split('#');
      var ass_id = parseInt(href_content[1]);
      var country_iso = href_content[2];
      var country_name = href_content[3];


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

        $('#assessment-results').click(function () {
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
                .attr('country_iso', function () {
                  continue_countries.push(element.country_iso);
                  return element.country_iso;
                })
                .appendTo(country_list);
            }
            removeStartedAssessments();
            handleContinueAssessment.call(self);

            if ($('#country-list-continue option').length <= 1) {
              $('#country-list-continue option').text('No assessments started');
              $('#continue-assessment').addClass('disabled');
            }

            //it's ugly but it works!
            if (country_iso != undefined && ass_id != undefined && country_name != undefined) {
              $('#country-list-continue').find('option[value="' + ass_id + '"]').attr("selected", "selected");
              $('#continue-assessment').click();
            }
          });
      }

      function removeStartedAssessments() {
        $('#country-list-new').find('option').each(function (index, item) {
          var country_iso = $(item).attr('value');
          if (continue_countries.indexOf(country_iso) != -1) {
            $(this).remove();
          }
        })
      }

      function handleCreateAssessment() {
        var self = this;

        $('#add-assessment').click(function (event) {
          var selected_country_iso = $('#country-list-new').find('option:selected').val();
          var selected_country_name = $('#country-list-new').find('option:selected').text();
          if (selected_country_iso !== '' && selected_country_name !== '') {
            createAssessment.call(self, selected_country_iso, selected_country_name);
          }
          else {
            $('#country-list-new').focus();
          }
        });
      }

      function handleContinueAssessment() {
        var self = this;

        $('#continue-assessment').click(function (event) {
          self.assessment_id = $('#country-list-continue').find('option:selected').val();
          var selected_country_name = $('#country-list-continue').find('option:selected').text();
          var selected_country_iso = $('#country-list-continue').find('option:selected').attr('country_iso');
          if (self.assessment_id !== '') {
            // return;
            continueAssessment.call(self, selected_country_iso, selected_country_name);
          }
          else {
            $('#country-list-continue').focus();
          }
        });
      }

      function createAssessment(country_iso, country_name) {
        var self = this;

        RequestService
          .createAssessment({ country: country_iso, user: user_id })
          .done(function (responseAssessment) {
            self.assessment_id = responseAssessment.id;
            $('#assessment-landing').hide();
            $('#assessment-results-btn').show();
            $('#assessment-edit').show();
            setAssessmentTitle(country_iso, country_name);
            getClassifications.call(self);
          });
      }

      function continueAssessment(country_iso, country_name) {
        $('#assessment-landing').hide();
        $('#assessment-edit').show();
        $('#assessment-results-btn').show();
        setAssessmentTitle(country_iso, country_name);
        getClassifications.call(this);
      }

      function setAssessmentTitle(country_iso, country_name) {
        var assessment_header = '<figure style="display:inline-block;width: 39px;margin-right: 1rem;" ><img style="margin-top: -10px;max-width: 100%; max-height: 100%;" src="/static/img/flags/' + country_iso.toLowerCase() + '.svg" /></figure>' + country_name;

        $('.page-menu .country').html(assessment_header);
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

      function renderClassifications(responseClassifications) {
        var accordion = $('#accordion')[0];
        accordion.innerHTML = '';

        for (var z = 0; z < responseClassifications.length; z++) {
          var classification = responseClassifications[z];
          var h3 = $('<h3>')
            .text(classification.name)
            .appendTo(accordion);
          var classification_menu = $('<classification-menu/>')
            .addClass('flex lcct-list classification-menu')
            .attr('role', 'menu')
            .attr('tabindex', '0');

          for (var j = 0; classification.second_level && j < classification.second_level.length; j++) {
            var subcat = classification.second_level[j];
            var previousClassification = z > 0 ? responseClassifications[z-1] : null; 
            var nextClassification = z < responseClassifications.length -1 ? responseClassifications[z+1] : null; 
            var currentClassification = responseClassifications[z]; 
            var classification_item = $('<classification-item/>')
              .addClass('toc-item lcct-list classification-item' + (j == 0 && z == 0 ? ' iron-selected' : ''))
              .attr('role', 'option')
              .attr('tabindex', '0')
              .attr('aria-disabled', 'false')
              .attr('aria-selected', 'true')
              .attr('data-id', subcat.id)
              .on('click', getQuestionsForCategory.bind(this
                                                          , classification.name
                                                          , subcat.name
                                                          , classification.second_level.length
                                                          , j
                                                          , previousClassification
                                                          , nextClassification
                                                          , currentClassification))
              .appendTo(classification_menu);
            var i_comp = $('<i/>')
              .text(j + 1)
              .addClass('lcct-list')
              .appendTo(classification_item);
            var p = $('<span/>')
              .text(subcat.name)
              .addClass('lcct-list')
              .appendTo(classification_item);
          }

          classification_menu.appendTo(accordion);
          // render the next questions button text to indicate the next questions set
          // this is done automatically at each click on next/prev buttons and also on clicking the categories
          // but it has to be set initially
          if(z === 0) {
            renderButtonsGoToCategoryText(classification.second_level[0], null, null, null);
          }
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

          if (!question.children) {
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

          if (question.children_yes) {
            renderQuestions.call(this
              , question.children_yes
              , show ? isShown(question, true) : show // will propagate false to all children
              , questions_container
              , questionClass + 'yes');
          }

          if (question.children_no) {
            renderQuestions.call(this
              , question.children_no
              , show ? isShown(question, false) : show
              , questions_container
              , questionClass + 'no');
          }

          if (question.children) {
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

        if (questions_container.innerHTML === '') {
          questions_container.innerHTML = 'No questions available';
        }
      }

      function isShown(element, buttonValue, force_show) {
        var response = false;

        if (force_show) {
          response = true;
        } else {
          if (!element.answer) {
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
        if (buttonVal) {
          return btn = !answer
            ? 'btn-default' : (JSON.parse(answer.value) && buttonVal)
              ? 'btn-primary' : 'btn-default';
        } else {
          return btn = !answer
            ? 'btn-default' : JSON.parse(answer.value)
              ? 'btn-default' : 'btn-primary';
        }
      }

      function handleAnswer(children_yes, children_no, isYesButton, questionClass, event) {
        var data = {
          'assessment': this.assessment_id,
          'question': $(event.currentTarget).attr('data-question'),
          'value': $(event.currentTarget).attr('data-value')
        };
        var answerId = $(event.currentTarget).attr('data-answer-id');
        if (children_yes) {
          for (var index = 0; index < children_yes.length; index++) {
            var element = children_yes[index];
            if (isYesButton) {
              $('#' + element.id).slideDown();
            } else {
              $('#' + element.id).slideUp();
            }
          }
        }

        if (children_no) {
          for (var index = 0; index < children_no.length; index++) {
            var element = children_no[index];
            if (isYesButton) {
              $('#' + element.id).slideUp();
            } else {
              $('#' + element.id).slideDown();
            }
          }
        }

        if (answerId) {
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

      function getQuestionsForCategory(classification_name, category_name, categories_no, index, previousClassification, nextClassification, currentClassification, event) {
        var elem = $(event.currentTarget);
        var all_elems = $('classification-item').removeClass('iron-selected');

        elem.addClass('iron-selected');
        classification_id = elem.attr('data-id');
        getQuestions.call(this, classification_id);
        renderTitleContent(classification_name, category_name, categories_no, index);
        handleGoToQuestions.call(this, false, false, index, categories_no, previousClassification, nextClassification, currentClassification);
      }

      $('.next_question').click(handleGoToQuestions.bind(this, true, true, null, null, null, null, null));
      $('.prev_question').click(handleGoToQuestions.bind(this, true, false, null, null, null, null, null));

      /**
       * this will be called when the user clicks the category (left side menu) or the next/prev button
       * - it will go to the desired category (questions set) and handle the next/prev buttons text and visibility
       * - when it is fired from the next/prev buttons, there is no context, and looking through the Dom will be used
       * - the Dom element that correspunds to the resired intention, being an jquery element, can be clicked, that will again call this function with the context
       * @param {boolean} shouldClick - only the next/prev button should click, since otherwise the click on category has already been fired
       * @param {boolean} goNext - indicates direction to go click a category, true for next and prev on false
       * @param {number} categoryIndex - each category clicked on the left side menu, know its index, the next/prev buttons don't
       * @param {number} categoriesNo - number of categories in the current classification, each category clicked on the left side menu, know its categoriesNo, the next/prev buttons don't
       * @param {Object} previousClassification - each category clicked on the left side menu, know its previousClassification, the next/prev buttons don't
       * @param {Object} previousClassification.second_level - this is the array of categories
       * @param {string} previousClassification.second_level[].name - name of category (questions set)
       * @param {Object} nextClassification - each category clicked on the left side menu, know its nextClassification, the next/prev buttons don't
       * @param {Object} currentClassification - each category clicked on the left side menu, know its currentClassification, the next/prev buttons don't
       */
      function handleGoToQuestions(shouldClick, goNext, categoryIndex, categoriesNo, previousClassification, nextClassification, currentClassification) {
        var categories = $('.ui-accordion-content-active classification-item');
        var classifications = $('.ui-accordion-header');
        var selectedCategoriesIndex = typeof categoryIndex === "number" ? categoryIndex : getQuestionCategoryIndex(categories);
        var categoriesLength = typeof categoriesNo === "number" ? categoriesNo : categories.length;
        var selectedClassificationsIndex = getSelectedClassificationsIndex(classifications);
        var prevNextCategory = getCategory(categories, selectedCategoriesIndex, currentClassification);
        var prevCateg = prevNextCategory.prevCateg;
        var nextCateg = prevNextCategory.nextCateg;        
        var isFirstCategory = selectedCategoriesIndex == 0;
        var isLastCategory = selectedCategoriesIndex == categoriesLength - 1;

        if (isFirstCategory) {
          renderButtonsGoToCategoryText(nextCateg, null, previousClassification, nextClassification);

          if(shouldClick) {
            var prevClassification = selectedClassificationsIndex > 0 ? classifications[selectedClassificationsIndex - 1] : null;
            goNext ? goToCategory(nextCateg, null, null) : goToCategory(null, prevClassification, 'last-of-type');
          }
        } else if (isLastCategory) {
          renderButtonsGoToCategoryText(null, prevCateg, previousClassification, nextClassification);

          if(shouldClick) {
            var nextClassification = selectedClassificationsIndex < classifications.length - 1 ? classifications[selectedClassificationsIndex + 1] : null;
            goNext ? goToCategory(null, nextClassification, 'first-of-type') : goToCategory(prevCateg, null, null);
          }
        } else {
          renderButtonsGoToCategoryText(nextCateg, prevCateg, null, null);

          if(shouldClick) {
            goNext ? goToCategory(nextCateg, null, null) : goToCategory(prevCateg, null, null);
          }
        }
      }

      /**
       * will set the text for the next/prev buttons and hide/show them if the do/dont't have text
       * will also show the name in next/prev category if needed
       * text is either present in nextCateg/prevCateg or will be taken from html elements
       * @param {Object} nextCateg 
       * @param {Object} prevCateg 
       * @param {Object} previousClassification 
       * @param {Object} nextClassification 
       */
      function renderButtonsGoToCategoryText(nextCateg, prevCateg, previousClassification, nextClassification) {
        var textNext = nextCateg ? nextCateg.name : nextClassification ? nextClassification.second_level[0].name : '';
        var textPrev = prevCateg ? prevCateg.name : previousClassification ? previousClassification.second_level[previousClassification.second_level.length - 1].name : '';

        if(textNext) {
          $('.next_question').show();
          $('.next_category').html(textNext);
        } else {
          $('.next_question').hide();
        }
        if(textPrev) {
          $('.prev_question').show();
           $('.prev_category').html(textPrev);
        } else {
          $('.prev_question').hide();
        }
      }

      /**
       * will return object with prevCategory and nextCategory, either an object from server or jquery dom element
       * @param {Object[]} categories - array of jquery dom elements
       * @param {number} selectedCategoriesIndex 
       * @param {Object} currentClassification 
       */
      function getCategory(categories, selectedCategoriesIndex, currentClassification) {
        var result = { prevCateg: null, nextCateg: null };

        if(currentClassification) {
          result.prevCateg = selectedCategoriesIndex > 0 ? currentClassification.second_level[selectedCategoriesIndex - 1] : null;
          result.nextCateg = selectedCategoriesIndex < currentClassification.second_level.length - 1 ? currentClassification.second_level[selectedCategoriesIndex + 1] : null;
        } else {
          result.prevCateg = categories[selectedCategoriesIndex - 1];
          result.nextCateg = categories[selectedCategoriesIndex + 1];
        }
        return result;
      }

      /**
       * will click the category and if need be, go the next classification to open
       * @param {Object} nextCateg 
       * @param {Object} nextClassification 
       * @param {string} attribute - used to search for first or last child in Dom elements for clicking after expanding a new category
       */
      function goToCategory(nextCateg, nextClassification, attribute) {
        try {
          if(nextCateg) {
            nextCateg.click();
          } else {
            var controls = $(nextClassification).attr('aria-controls');

            nextClassification.click();
            $('classification-menu#'+controls+'').find('classification-item:'+attribute).click();
          }
        } catch(e) {
        }
      }

      /**
       * find the index by looking in the dom for the 'iron-selected' class indicating the selected one
       * @param {Object[]} categories - array of jquery Dom elements representing the categories
       */
      function getQuestionCategoryIndex(categories) {
        var selectedCategoriesLength;

        categories.each(function (index, item) {
          if ($(item).hasClass('iron-selected')) {
            selectedCategoriesLength = index;
          }
        });
        return selectedCategoriesLength;
      }

      /**
       * find the index by looking in the dom for the 'ui-accordion-header-active' class indicating the selected one
       * @param {Object[]} classifications - array of jquery Dom elements representing the classifications
       */
      function getSelectedClassificationsIndex(classifications) {
        var selectedClassificationsIndex;

        classifications.each(function (index, item) {
          if ($(item).hasClass('ui-accordion-header-active')) {
            selectedClassificationsIndex = index;
          }
        });
        return selectedClassificationsIndex;
      }

      function renderTitleContent(classification_name, category_name, categories_no, index) {
        classification_title.html(classification_name);
        current.html(parseInt(index) + 1);
        last.html(categories_no);
        question_category.html(category_name);
      }
    });
});
