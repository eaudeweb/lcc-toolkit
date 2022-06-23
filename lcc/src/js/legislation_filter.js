$(document).ready(function() {

  let payload = {};
  let orderByOptions = {
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

  // set the page and consider the current order
  function activatePagination() {
    let selectedOrder = null;
    let selectedOrderValue = null;
    let found = false;

    $("ul.pagination li a").on('click', function() {
      Object.keys(orderByOptions).map(function(orderKey) {
        let queryMatch = window.location.search.match('\A?' + orderKey + '=[^&]*');
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
    let selectedOrderName = null;
    let selectedOrderValue = null;
    let selectedOrderKey = null;
    let found = false;

    Object.keys(orderByOptions).map(function(orderKey) {
      let queryMatch = window.location.search.match('\A?' + orderKey + '=[^&]*');
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

    let pageQueryMatch = window.location.search.match('\A?page=[^&]*');
    let pageNumber = pageQueryMatch ? pageQueryMatch[0].split('=')[1] : null;

    // set the 'active' class on the order that is currently selected
    $("ul.dropdown-menu-order li").addClass(function( index ) {
      let className =
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
      let orderName = $(this).attr('data-sort-id');
      let orderValue = $(this).attr('data-sort-dir');
      orderName !== 'relevance' ? payload[orderName] = orderValue : null;
      pageNumber ? payload['page'] = pageNumber : null;
      $(".submitBtn").click();
    });
  }

  function preselectFilters() {
    let filters = $("#filter-values").data("values");

    if(filters["q"]){
      payload["q"] = filters["q"][0];
      $("#textSearchInput").val(filters["q"][0]);
    }

    $("#classificationsSelect input").each(function(i, input){
      let $input = $(input);
      if($.inArray($input.val(), filters["classifications[]"]) >= 0){
        payload["classifications"] = filters["classifications[]"];
        $input.click();
        $input.closest('li').parents('li').find('i:first:not(.fa-caret-up)').click();
      }
    });

    $("#typeSelect input").each(function(i, input){
      let $input = $(input);
      if($.inArray($input.val(), filters["law_types[]"]) >= 0){
        payload["law_types"] = filters["law_types[]"];
        $input.click();
      }
    });

    payload["include_sections"] = $('#includeSections').is(":checked");

    $("#tagsSelect input").each(function(i, input){
      let $input = $(input);
      if($.inArray($input.val(), filters["tags[]"]) >= 0){
        payload["tags"] = filters["tags[]"];
        $input.click();
      }
    });

    $(".ms-drop input").each(function(i, input){
      let $input = $(input);
      if($.inArray($input.val(), filters["countries[]"]) >= 0){
        payload["countries"] = filters["countries[]"];
        $input.click();
      }
    });

    let min_year = $("#yearSlider").data("slider-min");
    let max_year = $("#yearSlider").data("slider-max");
    let from_year = $("#fromYear").val();
    let to_year = $("#toYear").val();

    if(from_year != min_year){
      payload["from_year"] = from_year;
    }

    if(to_year != max_year){
      payload["to_year"] = to_year;
    }
  }

  function send(payload) {
    let new_url = window.location.href.split('?')[0] + '?' + $.param(payload);

    window.location.href = new_url;
  }

  let classifications = [];
  let law_types = [];
  let tags = [];

  $('[data-toggle="popover"]').popover()
  $('.popoverDetails').on({
    'click': function() {
      $(this).popover('show');
    }
  });

  activatePagination();
  setOrderBy();
  setContentForEachPopover();

  function setContentForEachPopover() {
    const allPopovers = $('.popoverDetails');

    allPopovers.each(function( index ) {
      const id = $(this).attr('id');
      const itemDetails = $(this).attr('data-item');
      let fomattedDetails = handleNewLine(itemDetails);

      fomattedDetails = fomattedDetails.indexOf('http') !== -1 ? handleLink(fomattedDetails) : fomattedDetails;
      $(this)
      .attr({'data-content':`${fomattedDetails}`})
      .on('click', handleShowPopover(id)) // this is from common.js
    });

    // this is from common.js
    destroyPopoverOnFocusOut();
  }

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
    let $input = $(input);
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

  let slider_text = document.getElementById('yearSlider');

  let slider_values = [
    parseInt($('#yearSlider').attr('data-slider-min')),
    parseInt($('#yearSlider').attr('data-slider-max'))
  ]

  $("body").on('blur', '#fromYear, #toYear', function(e){
    let int_slider_values = [parseInt($('#fromYear').val()), parseInt($('#toYear').val())]
    $('#yearSlider').slider('setValue', int_slider_values)
  });

  // Activate select/deselect links for classification filters

  $('a.select-all').on('click', function(){
    $(this).closest('ul').find('input').prop('checked', true);
    $(this).closest('ul').find('input').each(function(i, input){
      let $input = $(input);
      classifications.push($input.val())
    });
    payload['classifications'] = classifications;
  });

  $('a.deselect-all').on('click', function(){
    $(this).closest('ul').find('input').prop('checked', false);
    $(this).closest('ul').find('input').each(function(i, input){
      let $input = $(input);
      let index = payload['classifications'].indexOf($input.val());
      if (index > -1) {
        payload['classifications'].splice(index, 1);
      }
    });
  });

  $('.classification-parrent').change(function(){
    if(this.checked) {
      $(this).closest('li').find('input').prop('checked', true);
      $(this).closest('li').find('input').each(function(i, input){
        let $input = $(input);
        classifications.push($input.val())
      });
      payload['classifications'] = classifications;
    } else {
      $(this).closest('li').find('input').prop('checked', false);
      $(this).closest('li').find('input').each(function(i, input){
        let $input = $(input);
        let index = payload['classifications'].indexOf($input.val());
        if (index > -1) {
          payload['classifications'].splice(index, 1);
        }
      });
    }
  });

  // Handle search and filters

  $('#textSearchInput').on('change', function() {
    let val = $(this).val();
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

  let observer = new MutationObserver(function(mutations) {
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

  $('#includeSections').on('change', function() {
    console.log($('#includeSections').is(":checked"))
    payload['include_sections'] = $('#includeSections').is(":checked");
    $(".submitBtn").click();
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
  const options = {
    submitCountryAttibutes: 'Save options'
  }

  filterCountryAttribute().updateFilterBasedOnURL(options, payload);
  filterCountryAttribute().attachListenerToModal(payload);
});
