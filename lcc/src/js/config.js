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