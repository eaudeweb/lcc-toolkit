
function filterCountryAttribute() {
  const countryAttributes = ['cw', 'small_cw', 'un', 'ldc', 'lldc', 'sid', 'region', 'sub_region', 'legal_system', 'population', 'hdi2015', 'gdp_capita', 'ghg_no_lucf', 'ghg_lucf'];

  const attachListenerToModal = function(payload, callback) {
    $('#exampleModal').on('show.bs.modal', function (event) {
      let submitButton = document.getElementById("submitCountryAttibutes");
      let allSelectList = document.getElementsByClassName("filter-country-attributes-select");

      //it will update payload object reference that it gets
      submitButton.addEventListener("click", function () {
        for (let index = 0; index < allSelectList.length; index++) {
          const selectElement = allSelectList[index];
          const selectedValue = selectElement.selectedOptions[0].value;
          const selectedLabel = selectElement.id;

          // it is single value select, so it will overwrite existing
          if(selectedValue) {
            payload[selectedLabel] = selectedValue;
          } else if(payload[selectedLabel]) {
            delete payload[selectedLabel];
          }

        }

        if(callback) {
          callback();
        }
      }, false);
    });
  }

  const updateFilterBasedOnURL = function() {
    const decodedURL = decodeURIComponent(window.location.search);

    countryAttributes.map((attribute) => {
      const attributeWithValue = decodedURL.match('\A?' + attribute + '=[^&]*');
      const attributeValue = attributeWithValue ? attributeWithValue[0].split('=')[1].replace('+', ' ') : null;
      if(attributeValue) {
        const selectDOMElement = document.getElementById(attribute);

        for (let i = 0; i < selectDOMElement.options.length; i++) {
          const option = selectDOMElement.options[i];
          if(option.value === attributeValue) {
            selectDOMElement.selectedIndex = i;
            break;
          }
        }        
      }
    });
  }

  return {
    attachListenerToModal,
    updateFilterBasedOnURL,
  }
}
