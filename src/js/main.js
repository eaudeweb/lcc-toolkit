function highlightChecked(item) {
    $parent = item.parent().parent().parent().parent('li').find('.list-header').first();
    $parent.addClass('selected')
    console.log($parent)
    if (!$parent.parent().hasClass('first-level')) {
        $recursion_item = $parent.find('input')
        highlightChecked($recursion_item)
    }
}

function removeHighlight(item) {
    $parent = item.parent().parent().parent().parent('li').find('.list-header').first();
    $checked = item.closest('ul').first().find("input:checked").length;
    if ($checked == 0)
        $parent.removeClass('selected')
    if (!$parent.parent().hasClass('first-level')) {
        $recursion_item = $parent.find('input')
        removeHighlight($recursion_item)
    }
}



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


    $(".check-fields .second-level input").change(function() {
        if (this.checked) {
            highlightChecked($(this))
        } else {
            removeHighlight($(this))
        }
    });
})