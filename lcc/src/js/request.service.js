/**
 * @module RequestService
 * Handles all requests and configures the ajax
 */
(function () {
  'use strict'
  LCCTModules.define('RequestService', ['Config'], function RequestService(Config){
      
    setTokenAJAX();

    // get cookie using jQuery
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
        contentType: Config.ajax_settings.contentType,
        dataType: Config.ajax_settings.dataType,
        beforeSend: function(xhr, settings) {

          if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader('X-CSRFToken', csrftoken);
          }
        }
      });
    }

    function getQuestions(category, assessment_pk) {

      var jqxhr = $.ajax({
        'type': 'GET',
        'url': Config.url.questions + category + '?assessment_pk=' + assessment_pk,
      });
      return jqxhr;
    }

    function getClassifications() {
      var jqxhr = $.ajax({
        'type': 'GET',
        'url': Config.url.classifications,
      });
      return jqxhr;
    }

    function createAnswer(data) {
      
      var jqxhr = $.ajax({
        'url': Config.url.answers,
        'type': 'POST',
        'data': JSON.stringify(data),
      })
      return jqxhr;
    }
  
    function updateAnswer(data, answerId) {
      
          var jqxhr = $.ajax({
            'url': Config.url.answers + answerId + '/',
            'type': 'PUT',
            'data': JSON.stringify(data),
          })
          return jqxhr;
        }
  
    function getAssessments() {
      
      var jqxhr = $.ajax({
        'url': Config.url.assessment,
        'type': 'GET',
      })
      return jqxhr;
    }

    function createAssessment(data) {
      
      var jqxhr = $.ajax({
        'url': Config.url.assessment,
        'type': 'POST',
        'data': JSON.stringify(data),
      })
      return jqxhr;
    }
  
    function getCountries() {
      
      var jqxhr = $.ajax({
        'url': Config.url.countries,
        'type': 'GET',
      })
      return jqxhr;
    }
                    

    return {
      getQuestions: getQuestions,
      getClassifications: getClassifications,
      createAnswer: createAnswer,
      updateAnswer: updateAnswer,
      getAssessments: getAssessments,
      createAssessment: createAssessment,
      getCountries: getCountries,
    }
  });
})();
