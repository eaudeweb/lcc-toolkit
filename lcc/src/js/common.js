

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
        if(statebutton.attr('functionality') == functionality[0]){
            $('#id_text').val(function(i, text) {
                if(selectedText.length == 0){
                    return text
                }
                if($(this).val().length == 0){
                    return selectedText;
                }
                else{
                    return text + '\n' + selectedText;
                }
            });
        }
        else{
            $('#id_text').val(function(i, text){
                if(selectedText.length == 0){
                    return text
                }
                else{
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
    $('body').on('click','.list-header', function(e) {
        if ($(e.target).attr('type') == "checkbox") {
            return
        }
        if ($(e.target).is('label')) {
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

    var textarea = $('textarea')
    if(textarea.length > 0){    
        var max_length = textarea.attr('maxlength');
        var current_length = textarea.val().length
         $("#rem_char").html((max_length - current_length) + " characters left");

        $('body').on("onchange keyup focus input", "textarea" , function() {
            updateTextarea()
        })
    }





    thisRespondHightlightText('#raw-text-page', $('.state button.active'))


    $('body').on('click','.state button', function(){
        $('.state button').removeClass('active')
        $(this).addClass('active')
    })

    if(($('#title').text().length > 49) && ($('#title').text().length < 73)) {
    	$('#title').css('font-size', 16+'px').css('line-height', '1.4').css('padding-top', 1.3 +"rem")
    }
    else if ( $('#title').text().length > 73) {
        $('#title').css('padding-top', '0')
    }

    $('.authenticated > span').click(function(){
        $('.actions-wrapper').animate({
            'width': 'toggle'
        })
    })
    $(".page-menu").sticky({topSpacing:0});
    $('.disabled').click(function(e){
        e.preventDefault();
    })
    var edited = false;
     $('input, textarea, select').on('change', function(){
        edited = true;

     })


    $('#special-button').click(function(e){
        if( edited == true ){
            if (confirm("Leaving the page will result in losing your modifications. \nPress ok if you want to leave") == true) {
                return true;
            } else {
                return false;
            }
        }
    })
})
