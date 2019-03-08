function getSelectionText() {
    var text = "";
    if (window.getSelection) {
        text = window.getSelection().toString();
    } else if (document.selection && document.selection.type != "Control") {
        text = document.selection.createRange().text;
    }
    return text;
}

function isIE() {
    userAgent = navigator.userAgent;
    return userAgent.indexOf("MSIE ") > -1 || userAgent.indexOf("Trident/") > -1 || userAgent.indexOf("Edge/") > -1;
}

var functionality = ['Append', 'Replace'];


function thisRespondHightlightText(thisDiv) {
    $('body').on("mouseup", thisDiv, function () {
        var statebutton = $('.state .active')
        var selectedText = getSelectionText();
        console.log(statebutton.attr('functionality'))
        if (statebutton.attr('functionality') == functionality[0]) {
            $('#id_text').val(function (i, text) {
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
            $('#id_text').val(function (i, text) {
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


function handleNewLine(testValue) {
    var resultWithNewLineTags = testValue.match(/\n/) ? replaceNewLine(testValue) : testValue.match(/\r/) ? replaceNewLine(testValue) : testValue;

    function replaceNewLine(itemValue) {
        var lines = itemValue.split('\n');
        var result = lines[0];
        for (let index = 1; index < lines.length; index++) {
            const element = lines[index];
            result += '<br>' + element;
        }
        return result;
    }
    return resultWithNewLineTags;
}

function handleLink(itemValue) {
    let result = itemValue;
    let all = result.substring(result.indexOf('http'), result.length).split(' ');
    for (let i = 0; i < all.length; i++) {
        const substr = all[i];
        result = substr.indexOf('http') > -1 ? result.replace(substr, '<a target="_blank" href=" ' + substr + '">' + substr + '</a>') : result;
    }
    return result;
}

function handleShowPopover(id) {
    console.log('handleShowPopover', id)
    return showPopoverForTheItem;

    function showPopoverForTheItem(event) {
        event.stopPropagation();
        $(`#${id}`).popover('show');
    }
}

function destroyPopoverOnFocusOut() {
    $(document).on("click", destroyPopover);

    function destroyPopover(e) {
        var container = $('.popover-content');

        // if the target of the click isn't the container nor a descendant of the container
        if (!container.is(e.target) && container.has(e.target).length === 0) {
            $('.popoverDetails').each(function (index) {
                $(this).popover('destroy');
            });
        }
    }
}

$(document).ready(function () {

    if (isIE()) {
        $('body').addClass('isIE');
    }


    $('body').on('click', '.list-header', function (e) {
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

        $('body').on("onchange keyup focus input", "textarea", function () {
            updateTextarea()
        })
    }





    thisRespondHightlightText('#raw-text-page')


    $('body').on('click', '.state button', function () {
        $('.state button').removeClass('active')
        $(this).addClass('active')
    })

    var edited = false;
    $('input, textarea, select').on('change', function () {
        edited = true;

    })


    $('#special-button').click(function (e) {
        if (edited == true) {
            if (confirm("Leaving the page will result in losing your modifications. \nPress ok if you want to leave") == true) {
                return true;
            } else {
                return false;
            }
        }
    })


    setTimeout(function () {
        $("#top-header").sticky({ topSpacing: 0 });
    }, 300)

    $('.disabled').click(function (e) {
        e.preventDefault();
    })

    if (window.matchMedia("(max-width: 760px)").matches) {
        $('meta[name="viewport"]').attr('content', 'width=' + 768);
    }

    $('.hidden_values ul li.original').each(function (index, item) {
        var value = $(item).html();
        var id = $(item).attr('id')
        $(item).remove()
        $('.assessment_table.edit').find('#' + id).append(value)
    })


    if ($('body').hasClass('assessment_profile')) {
        var links = $('.sources li a').clone()
        links.find('.remove_from_table').remove();
        var table_items = $('.assessment_table tbody tr td:first-of-type')

        table_items.each(function (index, item) {
            links.each(function (links_index, links_item) {
                if ($(item).attr('id') == $(links_item).attr('id')) {
                    $(item).append($(links_item))
                    return false
                }
            })
        })
    }


})