/**
 * @module LegalAssessmentResults
 * Handles the legal assesment results
 */
$(document).ready(function () {
    'use strict'
    LCCTModules.define('LegalAssessmentResults', ['Config', 'RequestService'],
        function LegalAssessmentResults(Config, RequestService) {


            this.assessment_id = window.location.pathname.split('/')[2];
            let gaps_no = 0;
            let sections_no = 0;
            let payload = {};
            const options = {
                submitCountryAttibutes: 'Apply filters'
            }


            getAssessmentResults.call(this);
            getAssessments.call(this);

            filterCountryAttribute().updateFilterBasedOnURL(options, payload);
            filterCountryAttribute().attachListenerToModal(payload, send.bind(null, payload));


            function send(payload) {
                let new_url = window.location.href.split('?')[0] + '?' + $.param(payload);

                window.location.href = new_url;
            }

            function getAssessments() {
                var self = this;
                RequestService
                    .getAssessments()
                    .done(function (all_assessments) {
                        var current_assessment;
                        for (var i = 0; i <= all_assessments.length; i++) {
                            var assesment = all_assessments[i];
                            if (assesment.id == self.assessment_id) {
                                current_assessment = assesment;
                                break;
                            }
                        }
                        setAssessmentTitle(current_assessment);
                        setBackAttr(current_assessment, self.assessment_id)
                    })
            }

            function setBackAttr(current_assessment, id) {
                var new_href = window.location.protocol + '//'
                    + window.location.host + '/'
                    + window.location.pathname.split('/')[1] + "/#"
                    + id + '#'
                    + current_assessment.country_iso + '#'
                    + current_assessment.country_name
                $('#back_btn').attr('href', new_href)
                console.log(new_href)
            }


            function setAssessmentTitle(assessment) {
                var assessment_header = '<figure style="display:inline-block;width: 39px;margin-right: 1rem;" ><img style="margin-top: -10px;max-width: 100%; max-height: 100%;" src="/static/img/flags/' + assessment.country_iso.toLowerCase() + '.svg" /></figure>' + assessment.country_name
                $('.results-header h2').html(assessment_header);
                $('.page-menu .country').html(assessment_header);
            }



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
                var h3 = $('<li>')
                    .html('<span>' + categories.length + '</span>' + (categories.length > 1 ? 'Categories' : ' Category'))
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
                    .html('<span>' + gaps_no + '</span>' + (gaps_no > 1 ? ' Areas of improvement' : ' Area of improvement'))
                    .appendTo(summary);
                var hsections = $('<li>')
                    .html('<span>' + sections_no + '</span>' + (sections_no > 1 ? ' Suggested examples' : ' Suggested example'))
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
                        .append($('<span>Key Terms</span>'))
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

                    var dd_suggestions = $('<dd/>')
                        .appendTo(dl_suggestions);

                    var dt_suggestion = $('<dt/>')
                        .appendTo(dl_suggestions);


                    var p_suggested_law = $('<p/>')
                        .text(question.sections.length + (question.sections.length > 1 ? ' Suggestions' : ' Suggestion'))
                        .appendTo(dd_suggestions);

                    sections_no += question.sections.length;
                    renderSuggestedLegislation(question.sections, dt_suggestion);

                    if (question.sections.length > 3) {
                        var button_title = '<span class="show">View all ' + question.sections.length + ' suggestions</span> <span class="hide">Show less suggestions</span>';
                        var toggle_legislation_results = $('<button type="button" class="btn btn-default results_toggle">' + button_title + '</button>')
                            .appendTo(container)
                            .click(handleToggleShowSugestions);

                    }
                }
            }

            function makeGapName(gap) {
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

            function renderSuggestedLegislation(sections, questions_container) {
                for (var s = 0; s < sections.length; s++) {
                    var section = sections[s];
                    var section_name = section.legislation.title + ' - ' + section.code;


                    var country = $('<span>')

                    var p2 = $('<p/>')
                        .appendTo(questions_container);
                    var a = $('<a/>')
                        .text(section_name)
                        .css("color", "#0052CC")
                        .attr('href', '/legislation/' + section.legislation.id + '/sections/#' + section.code)
                        .appendTo(p2);

                    var muted = $('<div/>')
                        .addClass('muted')
                        .append('<small>' + section.legislation.country_name + '  • ' + section.legislation.year + '</small>')
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

            function handleToggleShowSugestions() {
                var toggle_this = $(this).parent().find('.dl_suggestions dt p:nth-child(n+4)');
                toggle_this.animate({
                    'transform': 'translate3D(0,0,0)',
                    'height': 'toggle'
                })
                $(this).find('span').animate({
                    'opacity': 'toggle'
                }, 0)
            }



        });
});