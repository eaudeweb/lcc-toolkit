/**
 * @module LegalAssessmentResults
 * Handles the legal assesment results
 */
$(document).ready(function(){
  'use strict'
  LCCTModules.define('LegalAssessmentResults', ['Config', 'RequestService'], 
  function LegalAssessmentResults(Config, RequestService) {


    this.assessment_id = window.location.pathname.split('/')[2];
    var gaps_no = 0;
    var articles_no = 0;
    
    getAssessmentResults.call(this);

    function getAssessmentResults() {
      var self = this;
      RequestService
        .getAssessmentResults(this.assessment_id)
        .done(function (assessment_results) {
          renderAssessmentsResults(assessment_results);
      });
    }

    function renderAssessmentsResults(results) {
      renderClassifications(results.categories);
      handleAccordion();
    }

    function handleAccordion() {
      $('#accordion').accordion({
        collapsible: true,
        heightStyle: "content"
      });
    }

    
    function renderClassifications(categories) {
      var accordion = $('#accordion');
      var summary = $('#summary');
      var h3 = $('<h3>')
                .text(categories.length + (categories.length > 1 ? ' Categories' : ' Category'))
                .appendTo(summary);
      accordion.innerHTML = '';

      for (var z = 0; z < categories.length; z++) {
        var categorie = categories[z];
        var h3 = $('<h3>')
                  .text(categorie.name)
                  .appendTo(accordion);
        var classification_menu = $('<classification-menu/>')
                                  .addClass('flex lcct-list classification-menu')
                                  .attr('role', 'menu')
                                  .attr('tabindex', '0');

        renderQuestions(categorie.categories, classification_menu);
                                  
        classification_menu.appendTo(accordion);
      }
      var hgap = $('<h3>')
                .text(gaps_no + (gaps_no > 1 ? ' Gaps' : ' Gap'))
                .appendTo(summary);
      var harticles = $('<h3>')
                      .text(articles_no + (articles_no > 1 ? ' Law Suggestions' : ' Law Suggestion'))
                      .appendTo(summary);
    }

    function renderQuestions(categories, questions_container) {
      for (var index = 0; index < categories.length; index++) {
        var sub_categorie = categories[index];        
        var p_question_categ = $('<p/>')
                .text(sub_categorie.name)
                .css('font-weight', 'bold')
                .appendTo(questions_container);

        gaps_no += sub_categorie.questions.length;
        
        renderGaps(sub_categorie.questions, questions_container);
      }

    }

    function renderGaps(questions, questions_container) {
      for (var j = 0; j < questions.length; j++) {
        var question = questions[j];
        var answerId = question.answer ? question.answer.id : '';


        var li = $('<li/>')
                  .addClass('list-group-item question')
                  .attr('id', question.id)
                  .appendTo(questions_container);
        var p_question_text = $('<p/>')
                              .text(question.text)
                              .appendTo(li);
        var div = $('<div/>')
                  .addClass('btn-group question')
                  .attr('role', 'group')
                  .appendTo(li);
        var buttonYes = $('<button/>')
                        .text('Yes')
                        .addClass('btn ' + getBtnClass(true, question.answer))
                        .appendTo(div)
                        .attr('data-question', question.id)
                        .attr('data-value', 'true')
                        .attr('data-answer-id', answerId)
                          
        var buttonNo = $('<button/>')
                        .text('No')
                        .addClass('btn ' + getBtnClass(false, question.answer))
                        .attr('data-question', question.id)
                        .attr('data-value', 'false')
                        .attr('data-answer-id', answerId)
                        .appendTo(div)

        var gap_name = makeGapName(question.gap);
        
        var p_gap = $('<p/>')
                  .text(gap_name)
                  .css( "color", "red" )
                  .appendTo(questions_container);          
        var p_suggested_law = $('<p/>')
                .text(question.articles.length + (question.articles.length > 1 ? ' Suggested Legislations' : ' Suggested Legislation'))
                .appendTo(questions_container);
        
        articles_no += question.articles.length;
        renderSuggestedLegislation(question.articles, questions_container);
      }
    }

    function makeGapName(gap) {
      var gap_name = 'GAP ';
      for (var i = 0; i < gap.classifications.length; i++) {
        var classification = gap.classifications[i];

        gap_name += classification.name + (i == gap.classifications.length -1 ? '' : '|');
      }
      for (var j = 0; j < gap.tags.length; j++) {
        var tag = gap.tags[j];

        gap_name += tag.name + '|';
      }
      return gap_name;
    }

    function renderSuggestedLegislation(articles, questions_container) {
      
      for (var s = 0; s < articles.length; s++) {
        var article =  articles[s];
        var article_name = article.code + ' | ' + article.legislation.title + ' | ' +  article.legislation.country_name + ' ' + article.legislation.year;
        var p2 = $('<p/>')
        .appendTo(questions_container);

        var a = $('<a/>')
                .text(article_name)
                .css( "color", "blue" )
                .attr('href', '/legislation/' + article.legislation.id + '/articles/#' + article.code)
                .appendTo(p2);            
      }
    }
                    
    // btn-primary will suggest the existence of an answer
    // btn-default: no answer was given
    function getBtnClass(buttonVal, answer) {
      var btn;
      if(buttonVal) {
        return btn = answer ? 'btn-primary' : 'btn-default';
      } else {
        return btn = answer ? 'btn-default' : 'btn-primary';        
      }
    }
  });
});