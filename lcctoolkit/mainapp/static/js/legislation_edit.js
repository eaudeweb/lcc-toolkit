$(document).ready(function(){

  function set_upload_question_to_no() {
  	$("input[name=upload-question][value='No']").prop('checked', true);  
  }

  $(document).on('click',"#upload-question",function(){
    if ($(this).val() == "Yes") {
    	$("#upload_container_question").hide();
    	$("#upload_container_file").show();
    	$("input[name=pdf_file]").prop('required', true);
    }
  });

  $(document).on('click',"#renounce-upload",function(){
  	$("input[name=pdf_file]").prop('required', false);
  	$("#upload_container_file").hide();
  	$("#upload_container_question").show();
	set_upload_question_to_no()
  });

  set_upload_question_to_no();

});