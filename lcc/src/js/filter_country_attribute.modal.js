
function filterCountryAttribute() {
  const countryAttributes = ['cw', 'small_cw', 'un', 'ldc', 'lldc', 'sid', 'region', 'sub_region', 'legal_system', 'population', 'hdi2015', 'gdp_capita', 'ghg_no_lucf', 'ghg_lucf'];
  let contryAttributesSummary = 0;

  const attachListenerToModal = function(payload, callback) {

    $('#exampleModal').on('show.bs.modal', function (event) {
      let submitButton = document.getElementById("submitCountryAttibutes");
      let allSelectList = document.getElementsByClassName("filter-country-attributes-select");

      //it will update payload object reference that it gets
      submitButton.addEventListener("click", function () {
        contryAttributesSummary = 0;
        console.log('rrr')
        console.log('allSelectList', allSelectList)
        console.log('payload', payload)

        for (let index = 0; index < allSelectList.length; index++) {
          const selectElement = allSelectList[index];
          const selectedValue = selectElement.selectedOptions[0].value;
          const selectedLabel = selectElement.id;
          console.log('selectElement', selectElement)
          console.log('selectedValue', selectedValue)
          console.log('selectedLabel', selectedLabel)

          // it is single value select, so it will overwrite existing
          if(selectedValue) {
            payload[selectedLabel] = selectedValue;
            contryAttributesSummary++;
          } else if(payload[selectedLabel]) {
            delete payload[selectedLabel];
          }

        }
        updateContryAttributesSummary();
        if(callback) {
          callback();
        }
      }, false);
    });
  }

  const updateFilterBasedOnURL = function(options, payload) {
    const decodedURL = decodeURIComponent(window.location.search);
    contryAttributesSummary = 0;

    if(options) {
      Object.keys(options).map((key) => {
        document.getElementById(key).innerText = options[key];
      })
    }

    countryAttributes.map((attribute) => {
      const listOfParams = decodedURL.replace('?','').split('&')
      const attributeValueItem = listOfParams.find((param) => param.split('=')[0] === attribute);
      const attributeValue = attributeValueItem ? attributeValueItem.split('=')[1].replace('+',' ') : null;

      if(attributeValue) {
        const selectDOMElement = document.getElementById(attribute);

        for (let i = 0; i < selectDOMElement.options.length; i++) {
          const option = selectDOMElement.options[i];
          if(option.value === attributeValue) {
            selectDOMElement.selectedIndex = i;
            payload[attribute] = attributeValue;
            break;
          }
        }
        contryAttributesSummary++;
      }
    });
    updateContryAttributesSummary();
  }

  const updateContryAttributesSummary = function() {
    document.getElementById('contryAttributesSummary').innerText = contryAttributesSummary > 0 ? `${contryAttributesSummary} attributes selected` : 'No attributes selected';
  }

  return {
    attachListenerToModal,
    updateFilterBasedOnURL,
  }
}
