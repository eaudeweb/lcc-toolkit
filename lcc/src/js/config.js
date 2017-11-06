/**
 * @module Config
 * Handles the Config functionality
 */
(function () {
  'use strict'
  LCCTModules.define('Config', [], function Config(){

    var url = {
     'classifications':'/api/classification',
     'answers':'/api/answers/',
     'questions':'/api/question-category/',
     'assessment':'/api/assessments/',
     'countries':'/api/countries/',
     'assessment_results':'/legal-assessment/pk/results',
     'api_assessment_results':'/api/assessments/pk/results/',
     'assessment_profile':'/country/pk/'
    }

    var ajax_settings = {
     'contentType':'application/json',
     'dataType':'json',
    }


    return {
      url: url,
      ajax_settings: ajax_settings
    }
  });
})();
