$(document).ready(function(){
	
	function auth_input_focus() {
	  	$('#user-empty-error-msg').addClass("hidden");
	  	$('#auth-failed-error-msg').addClass('hidden');
	}

	$("input[name=username]").focus(auth_input_focus);
	$("input[name=password]").focus(auth_input_focus);

	$("#login-btn").click(function(e){

	  var formData = $('#login-form').serialize(); 
	  var username = $('input[name=username]').val();
	  var password = $('input[name=password').val();

	  e.preventDefault();

	  if ((username.length == 0) || (password.length == 0)) {
	  	$('#user-empty-error-msg').removeClass("hidden");
	  	return false;
	  }

	  $.ajax({
	    type: 'POST', 
	    url: '/login/',
	    cache: false,
	    dataType: 'json',
	    data: formData,
	    success: 
	    	function (data) {
	    	},
	    error:
	    	function(xhr, ajaxOptions, thrownError) {
				abort("Error:" + xhr.status +  thrownError);
	    	}
	  });

	  return false;

	});
});