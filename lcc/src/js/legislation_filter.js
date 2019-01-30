var payload = {};
var orderByOptions = {
    relevance: 'Relevance',
    promulgation_sort: {
        '1': 'Promulgation asc',
        '-1': 'Promulgation desc'
    },
    country_sort: {
        '1': 'Country asc',
        '-1': 'Country desc'
    }
}
var allQueryParams = '/([^?=&]+)(=([^&]*))?/g';
// var matchOneQueryParam = `\A?${queryName}=[^&]*`;

// set the page and consider the current order
function activatePagination() {
    var selectedOrder = null;
    var selectedOrderValue = null;
    var found = false;

    $("ul.pagination li a").on('click', function() {
        Object.keys(orderByOptions).map(function(orderKey) {
            var queryMatch = window.location.search.match('\A?' + orderKey + '=[^&]*');
            selectedOrder = !found && !!queryMatch ? orderKey : selectedOrder;
            selectedOrderValue = !found && !!queryMatch ? queryMatch[0].split('=')[1] : selectedOrderValue;
            found = !! selectedOrder;
        });
        !!selectedOrder ? payload[selectedOrder] = selectedOrderValue : null;

        payload['page'] = $(this).attr('data-page');
        $(".submitBtn").click();
    });
}

function setOrderBy() {
    var selectedOrderName = null;
    var selectedOrderValue = null;
    var selectedOrderKey = null;
    var found = false;

    Object.keys(orderByOptions).map(function(orderKey) {
        var queryMatch = window.location.search.match('\A?' + orderKey + '=[^&]*');
        // if found query, change, if not keep as it was
        selectedOrderName = !found ?
                                queryMatch ? orderByOptions[orderKey][queryMatch[0].split('=')[1]] : ''
                            : selectedOrderName;
        found = !!selectedOrderName;

        // if found query, change, if not keep as it was
        selectedOrderKey = queryMatch ? orderKey : selectedOrderKey;

        // if found query, change, if not keep as it was
        selectedOrderValue = queryMatch ? queryMatch[0].split('=')[1] : selectedOrderValue;
    });

    selectedOrderName = selectedOrderName ? selectedOrderName : orderByOptions.relevance;
    selectedOrderKey = selectedOrderKey ? selectedOrderKey : 'relevance';
    selectedOrderValue = selectedOrderValue ? selectedOrderValue : '';

    var pageQueryMatch = window.location.search.match('\A?page=[^&]*');
    var pageNumber = pageQueryMatch ? pageQueryMatch[0].split('=')[1] : null;

    // set the 'active' class on the order that is currently selected
    $("ul.dropdown-menu-order li").addClass(function( index ) {
        var className = 
            $(this).children( "a" ).attr('data-sort-id') === selectedOrderKey &&
            $(this).children( "a" ).attr('data-sort-dir') === selectedOrderValue ?
                "active" : '';
        return className;
    });

    // set the name of the preselected order
    $("#orderBySelected").text(selectedOrderName);

    // set the active class on the list of order option, to open it
    $("#orderByBtn").on('click', function showOptions() {
        $("#orderByParent").addClass( "active" )
    });

    // remove the 'active' class, to close the list on blur
    $("#orderByBtn").on('blur', function showOptions() {
        $("#orderByParent").removeClass( "active" )
    });

    // on lick set the payload and click the submit to reflect the order and the page
    $("ul.dropdown-menu-order li a").on('click', function() {
        var orderName = $(this).attr('data-sort-id');
        var orderValue = $(this).attr('data-sort-dir');
        
        orderName !== 'relevance' ? payload[orderName] = orderValue : null;
        pageNumber ? payload['page'] = pageNumber : null;
        $(".submitBtn").click();
    });
}

function findOrderQueryParam(params) {
    
}

function preselectFilters() {
    var filters = $("#filter-values").data("values");
    var stop = 0;

    if(filters["q"]){
      payload["q"] = filters["q"][0];
      $("#textSearchInput").val(filters["q"][0]);
    }

    $("#classificationsSelect input").each(function(i, input){
      var $input = $(input);
      if($.inArray($input.val(), filters["classifications[]"]) >= 0){
        payload["classifications"] = filters["classifications[]"];
        $input.click();
        $input.closest('li').parents('li').find('i:first:not(.fa-caret-up)').click();
      }
    });

    $("#typeSelect input").each(function(i, input){
      var $input = $(input);
      if($.inArray($input.val(), filters["law_types[]"]) >= 0){
        payload["law_types"] = filters["law_types[]"];
        $input.click();
      }
    });

    $("#tagsSelect input").each(function(i, input){
      var $input = $(input);
      if($.inArray($input.val(), filters["tags[]"]) >= 0){
        payload["tags"] = filters["tags[]"];
        $input.click();
      }
    });

    $(".ms-drop input").each(function(i, input){
      var $input = $(input);
      if($.inArray($input.val(), filters["countries[]"]) >= 0){
        payload["countries"] = filters["countries[]"];
        $input.click();
      }
    });

    var min_year = $("#yearSlider").data("slider-min");
    var max_year = $("#yearSlider").data("slider-max");
    var from_year = $("#fromYear").val();
    var to_year = $("#toYear").val();

    if(from_year != min_year){
      payload["from_year"] = from_year;
    }

    if(to_year != max_year){
      payload["to_year"] = to_year;
    }
}

function send(payload) {
    var new_url = window.location.href.split('?')[0] + '?' + $.param(payload);
    console.log(new_url);
    window.location.href = new_url;
}

$(document).ready(function() {

    var classifications = [];
    var countries = [];
    var law_types = [];
    var tags = [];

    var autocomplete = [];

    activatePagination();
    setOrderBy();

    // Activate multiselect
    $('#countrySelect').multipleSelect({
        width: '100%',
        multiple: true,
        multipleWidth: 260,
        filter: true
    });
    $('.ms-search').append(
        '<div class="search-icon">\
        <i class="fa fa-search" aria-hidden="true"></i>\
        </div>'
    );

    // Activate Slider
    $("#yearSlider").slider({formatter: function(value) {
      return value;
    }});

    $("#yearSlider").on("slide", function(slideEvt) {
      $("#fromYear").val(slideEvt.value[0]);
      $("#toYear").val(slideEvt.value[1]);
      payload['from_year'] = slideEvt.value[0];
      payload['to_year'] = slideEvt.value[1];
    });

    preselectFilters();

    $(".third-level input").each(function(i, input){
      var $input = $(input);
      $input
        .click(function(){
          if ($input.prop('checked')){
            $input
              .closest('ul')
              .siblings('span')
              .find('> input:first-child')
              .prop('checked', true);
          }
        });
    });

    var slider_text = document.getElementById('yearSlider');

    var slider_values = [
        parseInt($('#yearSlider').attr('data-slider-min')),
        parseInt($('#yearSlider').attr('data-slider-max'))
    ]

    var observer = new MutationObserver(function(mutations) {
        slider_values = slider_text.getAttribute('value').split(',');
        slider_values = [parseInt(slider_values[0]),parseInt(slider_values[1])]
        $("#fromYear").val(slider_values[0]);
        $("#toYear").val(slider_values[1]);
        payload['from_year'] = slider_values[0];
        payload['to_year'] = slider_values[1];
    });
    observer.observe(slider_text, {
      attributes: true,
      attributeFilter: ['value']
    });


    $("body").on('blur', '#fromYear, #toYear', function(e){
      var int_slider_values = [parseInt($('#fromYear').val()), parseInt($('#toYear').val())]
      console.log(int_slider_values)
      $('#yearSlider').slider('setValue', int_slider_values)
    });


    // Activate autocomplete

    $("#classificationsSelect > li.first-level > span > label").each(function(){
      autocomplete.push({
        id: $(this).attr('for'),
        name: $(this).html()
      });
    });

    $("#tagsSelect > li label").each(function(){
      autocomplete.push({
        id: $(this).attr('for'),
        name: $(this).html()
      });
    });

    $('#textSearchInput').easyAutocomplete({
      data: autocomplete,
      getValue: 'name',
      list: {
        maxNumberOfElements: 5,
        match: {
          enabled: true
        },
        onChooseEvent: function() {
          var id = $("#textSearchInput").getSelectedItemData().id;
          $("#" + id).click();
          $("#textSearchInput").val('').change();
        }
      }
    });
    $('div.easy-autocomplete').removeAttr('style');

    // Activate select/deselect links for classification filters

    $('a.select-all').on('click', function(){
      $(this).closest('ul').find('input').prop('checked', true);
    });

    $('a.deselect-all').on('click', function(){
      $(this).closest('ul').find('input').prop('checked', false);
    });

    // Handle search and filters

    $('#textSearchInput').on('change', function() {
      var val = $(this).val();
      if(val){
        payload['q'] = val;
      } else {
        delete payload['q'];
      }
    });

    // Activate Slider
    $("#yearSlider").slider({
        formatter: function(value) {
            return value;
        }
    });

    $("#yearSlider").on("slide", function(slideEvt) {
        $("#fromYear").val(slideEvt.value[0]);
        $("#toYear").val(slideEvt.value[1]);
        payload['from_year'] = slideEvt.value[0];
        payload['to_year'] = slideEvt.value[1];
    });

    var slider_text = document.getElementById('yearSlider');

    var slider_values = [1945, 2017]

    var observer = new MutationObserver(function(mutations) {
        slider_values = slider_text.getAttribute('value').split(',');
        slider_values = [parseInt(slider_values[0]), parseInt(slider_values[1])]
        $("#fromYear").val(slider_values[0]);
        $("#toYear").val(slider_values[1]);
        payload['from_year'] = slider_values[0];
        payload['to_year'] = slider_values[1];
    });
    try {
      // statements
      observer.observe(slider_text, {
          attributes: true,
          attributeFilter: ['value']
      });
    } catch(e) {
      console.log(e);
    }


    $("body").on('blur', '#fromYear, #toYear', function(e) {
        var int_slider_values = [parseInt($('#fromYear').val()), parseInt($('#toYear').val())]
        console.log(int_slider_values)
        $('#yearSlider').slider('setValue', int_slider_values)
    });


    // Activate autocomplete

    $("#classificationsSelect > li.first-level > span > label").each(function() {
        autocomplete.push({
            id: $(this).attr('for'),
            name: $(this).html()
        });
    });

    $("#tagsSelect > li label").each(function() {
        autocomplete.push({
            id: $(this).attr('for'),
            name: $(this).html()
        });
    });

    $('#textSearchInput').easyAutocomplete({
        data: autocomplete,
        getValue: 'name',
        list: {
            maxNumberOfElements: 5,
            match: {
                enabled: true
            },
            onChooseEvent: function() {
                var id = $("#textSearchInput").getSelectedItemData().id;
                $("#" + id).click();
                $("#textSearchInput").val('').change();
            }
        }
    });
    $('div.easy-autocomplete').removeAttr('style');

    $('#textSearchInput').on('change', function() {
        var val = $(this).val();
        if (val) {
            payload['q'] = val;
        } else {
            delete payload['q'];
        }
    });

    $('#classificationsSelect input').on('change', function() {
        if ($(this).is(':checked')) {
            if ($.inArray($(this).val()) == -1) {
                classifications.push($(this).val())
            }
        } else {
            classifications.splice(classifications.indexOf($(this).val(), 1))
        }
        payload['classifications'] = classifications;
    });

    $('#countrySelect').on('change', function() {
        payload['countries'] = $(this).val();
    });

    $('#typeSelect input').on('change', function() {
        if ($(this).is(':checked')) {
            if ($.inArray($(this).val()) == -1) {
                law_types.push($(this).val())
            }
        } else {
            law_types.splice(law_types.indexOf($(this).val(), 1))
        }
        payload['law_types'] = law_types;
    });

    $('#tagsSelect input').on('change', function() {
        if ($(this).is(':checked')) {
            if ($.inArray($(this).val()) == -1) {
                tags.push($(this).val())
            }
        } else {
            tags.splice(tags.indexOf($(this).val(), 1))
        }
        payload['tags'] = tags;
    });

    $('.submitBtn').on('click', function() {
        send(payload);
    });

    $('#textSearchInput').on('keyup', function(e) {
        if (e.which == 13) {
            send(payload);
        }
    });
});
