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


function getSelectionText() {
    var text = "";
    if (window.getSelection) {
        text = window.getSelection().toString();
    } else if (document.selection && document.selection.type != "Control") {
        text = document.selection.createRange().text;
    }
    return text;
}


var functionality = ['Append', 'Replace'];


function thisRespondHightlightText(thisDiv, statebutton){
   $('body').on("mouseup", thisDiv , function () {
        var selectedText = getSelectionText();
        if(statebutton.html() == functionality[0]){
            $('#id_text').val(function(i, text) {
                if(selectedText.length == 0)
                    return text
                if($(this).val().length == 0){
                    return selectedText;
                }
                else
                    return text + '\n' + selectedText;
            });
        }
        else{
            $('#id_text').val(function(i, text){
                if(selectedText.length == 0)
                    return text
                else
                    return selectedText
            });
        }
    });
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

    $('body').on("change keyup input", "textarea" , function() {
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

    $('.state button').html(functionality[0])

    thisRespondHightlightText('#raw-text-page', $('.state button'))


    $('body').on('click','.state button', function(){
        if($(this).html() == functionality[0])
            $(this).html(functionality[1])
        else
            $(this).html(functionality[0])
    })


    $lastestClass = $('.classificaions').find('input:checked')
    $lastestClass.each(function(){
        highlightChecked($(this))
    })

    $lastestTag = $('.tags').find('input:checked')
    $lastestTag.each(function(){
        highlightChecked($(this))
    })

    $('.authenticated > span').click(function(){
        $('.actions-wrapper').animate({
            'width': 'toggle'
        })
    })
    $(".page-menu").sticky({topSpacing:0});
})
