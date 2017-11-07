/**
 * @module LegalAssessmentResults
 * Handles the legal assesment results
 */
$(document).ready(function() {
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
                    .done(function(assessment_results) {
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
                var h3 = $('<li>')
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
                var hgap = $('<li>')
                    .text(gaps_no + (gaps_no > 1 ? ' Areas of improvement' : ' Area of improvement'))
                    .appendTo(summary);
                var harticles = $('<li>')
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

                    var container = $('<div/>')
                        .addClass('question-wrapper')
                        .appendTo(questions_container);

                    var question_content = $('<div/>')
                        .addClass('list-group-item question')
                        .attr('id', question.id)
                        .appendTo(container);

                    var p_question_text = $('<p/>')
                        .text(question.text)
                        .appendTo(question_content);
                    var div = $('<div/>')
                        .addClass('btn-group question')
                        .attr('role', 'group')
                        .appendTo(question_content);
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

                    var dl_gap = $('<dl/>')
                        .addClass('dl_gap')
                        .appendTo(container);

                    var dd_gap = $('<dd/>')
                        .append($('<span>Area of improvement</span>'))
                        .appendTo(dl_gap);

                    var dt_gap = $('<dt/>')
                        .appendTo(dl_gap);

                    var p_gap = $('<p/>')
                        .text(gap_name)
                        .css("color", "#f34e2a")
                        .appendTo(dt_gap);


                    var dl_suggestions = $('<dl/>')
                        .addClass('dl_suggestions')
                        .appendTo(container);

                    var dd_suggestions  = $('<dd/>')
                        .appendTo(dl_suggestions);

                    var dt_suggestion = $('<dt/>')
                        .appendTo(dl_suggestions);


                    var p_suggested_law = $('<p/>')
                        .text(question.articles.length + (question.articles.length > 1 ? ' Suggestions' : ' Suggestion'))
                        .appendTo(dd_suggestions);

                    articles_no += question.articles.length;
                    renderSuggestedLegislation(question.articles, dt_suggestion);

                    if( question.articles.length > 3 ) {
                      var button_title = '<span class="show">View all ' + question.articles.length + ' suggestions</span> <span class="hide">Show less suggestions</span>';                 
                      var toggle_legislation_results = $('<button type="button" class="btn btn-default results_toggle">'+button_title+'</button>')
                                                      .appendTo(container)
                                                      .click(handleToggleShowSugestions);  

                    }
                }
            }

            function makeGapName(gap) {
              console.log(gap)
                var gap_name = '• ';
                for (var i = 0; i < gap.classifications.length; i++) {
                    var classification = gap.classifications[i];

                    gap_name += classification.name + (i == gap.classifications.length - 1 ? '' : ' | ');
                }
                for (var j = 0; j < gap.tags.length; j++) {
                    var tag = gap.tags[j];

                    gap_name += tag.name + ' | ';

                }
                return gap_name;
            }

            function renderSuggestedLegislation(articles, questions_container) {

                for (var s = 0; s < articles.length; s++) {
                    var article = articles[s];
                    console.log(article)
                    var article_name =  article.legislation.title + ' - ' + article.code;


                    var country = $('<span>')

                    var p2 = $('<p/>')
                        .appendTo(questions_container);
                    var a = $('<a/>')
                        .text(article_name)
                        .css("color", "#0052CC")
                        .attr('href', '/legislation/' + article.legislation.id + '/articles/#' + article.code)
                        .appendTo(p2);

                    var muted = $('<div/>')
                                .addClass('muted')
                                .append('<small>'+article.legislation.country_name + '  • ' +article.legislation.year+'</small>')
                                .appendTo(p2);
                    
                }
            }

            // btn-primary will suggest the existence of an answer
            // btn-default: no answer was given
            function getBtnClass(buttonVal, answer) {
                var btn;
                if (buttonVal) {
                    return btn = answer ? 'btn-primary' : 'btn-default';
                } else {
                    return btn = answer ? 'btn-default' : 'btn-primary';
                }
            }

            function handleToggleShowSugestions(){
                var toggle_this = $(this).parent().find('.dl_suggestions dt p:nth-child(n+4)');
                toggle_this.animate({
                    'transform': 'translate3D(0,0,0)',
                    'height': 'toggle'
                })
                $(this).find('span').animate({
                    'opacity': 'toggle'
                },0)
            }


        });
});