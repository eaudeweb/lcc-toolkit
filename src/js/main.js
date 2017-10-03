function highlightChecked(item) {
    $parent = item.parent().parent().parent().parent('li').find('.list-header').first();
    if($parent.length == 0)
        return

    $parent.addClass('selected')

    if (!$parent.parent().hasClass('first-level')) {
        $recursion_item = $parent.find('input')
        highlightChecked($recursion_item)
    }
}

function removeHighlight(item) {
    $parent = item.parent().parent().parent().parent('li').find('.list-header').first();
    if($parent.length == 0)
        return
    $checked = item.closest('ul').first().find("input:checked").length;
    if ($checked == 0)
        $parent.removeClass('selected')
    if (!$parent.parent().hasClass('first-level')) {
        $recursion_item = $parent.find('input')
        removeHighlight($recursion_item)
    }
}



$(document).ready(function() {
    $('body').on('click','.list-header', function(e) {
        if ($(e.target).attr('type') == "checkbox") {
            return
        }
        $(this).parent().toggleClass('expanded');
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


    $(".check-fields input").change(function() {
        if (this.checked) {
            highlightChecked($(this))
            // $(this).parent().addClass('selected')
        } else {
            removeHighlight($(this))
            // $(this).parent().removeClass('selected')

        }
    });

    $lastestClass = $('.classificaions').find('input:checked')
    $lastestClass.each(function(){
        highlightChecked($(this))
    })

    $lastestTag = $('.tags').find('input:checked')
    $lastestTag.each(function(){
        highlightChecked($(this))
    })
})
