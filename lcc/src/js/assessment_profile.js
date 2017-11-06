/**
 * @module LegalAssessmentProfile
 * Handles the legal assesment results
 */
$(document).ready(function(){
    'use strict'
    LCCTModules.define('LegalAssessmentProfile', ['Config', 'RequestService'], 
    function LegalAssessmentProfile(Config) {
        this.country_iso = null;

        $('#assess_profile_country_list').change(handleChangeCountry.bind(self));

        function handleChangeCountry(event) {
            this.country_iso= $(event.currentTarget).find('option:selected').val();
            document.location.href = Config.url.assessment_profile.replace('pk', this.country_iso);            
          }
    });
});