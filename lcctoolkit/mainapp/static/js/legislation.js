$(document).ready(function(){

	function add_pdf_browser_html() {	
		$('#pdf-file-selector').html($('#select-pdf-file-html').html());
	}
	
	function ask_user_if_upload_needed_set_html() {
		$('#pdf-file-selector').html($('#ask-if-upload-pdf-file').html());
	}
	
	function ask_user_if_upload_needed_set_handlers() {
		$('input[name=upload-new-pdf-file]').on("click", function() {
			var answer = $(this).val();
			if (answer == "yes") {
				add_pdf_browser_html();
						add_pdf_browser_html_show_skip_link();
			}
	    });
	}
	
	function setup_upload_needed_question() {
		ask_user_if_upload_needed_set_html();
		ask_user_if_upload_needed_set_handlers();
	}
		 

	$("#save-btn").click(function(e){		
		$("#in-progress-msg").removeClass("hidden");
	});
	
	
	if ($('#have-validation-errors').text().length == 0) {
		add_pdf_browser_html();
	}
	else {
		setup_upload_needed_question();
	}
	
});