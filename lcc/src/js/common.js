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


function thisRespondHightlightText(thisDiv) {
    $('body').on("mouseup", thisDiv, function() {
        var statebutton = $('.state .active')
        var selectedText = getSelectionText();
        console.log(statebutton.attr('functionality'))
        if (statebutton.attr('functionality') == functionality[0]) {
            $('#id_text').val(function(i, text) {
                if (selectedText.length == 0) {
                    return text
                }
                if ($(this).val().length == 0) {
                    return selectedText;
                } else {
                    return text + '\n' + selectedText;
                }
            });
        } else {
            $('#id_text').val(function(i, text) {
                if (selectedText.length == 0) {
                    return text
                } else {
                    return selectedText
                }
            });
        }
        $('textarea').focus()
    });
}

function updateTextarea() {
    var textarea = $('textarea')
    var max_length = textarea.attr('maxlength');
    var current_length = textarea.val().length
    $("#rem_char").html((max_length - current_length) + " characters left");
}

$(document).ready(function() {
    $('body').on('click', '.list-header', function(e) {
        if ($(e.target).attr('type') == "checkbox") {
            return
        }
        if ($(e.target).is('label')) {
            return
        }
        $(this).parent().toggleClass('collapsed');
        $checkbox = $(this).find('i').first();
        $sub_level = $(this).parent().find('ul').first();
        $sub_level.animate({
            'height': 'toggle'
        })
        $checkbox.toggleClass('fa-caret-up')
    })

    var textarea = $('textarea')
    if (textarea.length > 0) {
        var max_length = textarea.attr('maxlength');
        var current_length = textarea.val().length
        $("#rem_char").html((max_length - current_length) + " characters left");

        $('body').on("onchange keyup focus input", "textarea", function() {
            updateTextarea()
        })
    }





    thisRespondHightlightText('#raw-text-page')


    $('body').on('click', '.state button', function() {
        $('.state button').removeClass('active')
        $(this).addClass('active')
    })

    var edited = false;
    $('input, textarea, select').on('change', function() {
        edited = true;

    })


    $('#special-button').click(function(e) {
        if (edited == true) {
            if (confirm("Leaving the page will result in losing your modifications. \nPress ok if you want to leave") == true) {
                return true;
            } else {
                return false;
            }
        }
    })


    setTimeout(function() {
        $("#top-header").sticky({ topSpacing: 0 });
    }, 300)

    $('.disabled').click(function(e) {
        e.preventDefault();
    })

    if (window.matchMedia("(max-width: 760px)").matches) {
        $('meta[name="viewport"]').attr('content', 'width=' + 768);
    }

    $('.hidden_values ul li.original').each(function(index,item){
        var value = $(item).html();
        var id = $(item).attr('id')
        $(item).remove()
        $('.assessment_table.edit').find('#'+id).append(value)
    })


})