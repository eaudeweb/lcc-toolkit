$(document).ready(function() {
    $('.list-header').on('click', function(e) {
        if ($(e.target).attr('type') == "checkbox") {
            return
        }

        $checkbox = $(this).find('i').first();
        $sub_level = $(this).parent().find('ul').first();
        $sub_level.animate({
            'height': 'toggle'
        })
        $checkbox.toggleClass('fa-minus-square')
    })

 	$("#rem_char").html("1024 characters left");

    $('textarea').keyup(function() {
        $("#rem_char").html((1024 - this.value.length) + " characters left");
    })
})


