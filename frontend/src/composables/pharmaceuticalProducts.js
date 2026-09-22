export function usePharmaceuticalProducts() {
  const getIngredientName = (ingredient, substanceNameOnly = false) => {
    const substanceName = ingredient.active_substance.inn
      ? ingredient.active_substance.inn
      : ingredient.active_substance.long_number
        ? ingredient.active_substance.long_number
        : ingredient.active_substance.short_number
          ? ingredient.active_substance.short_number
          : ingredient.active_substance.unii
            ? ingredient.active_substance.unii.substance_unii
            : ingredient.active_substance.analyte_number
              ? ingredient.active_substance.analyte_number
              : '?'
    let result = substanceName
    if (!substanceNameOnly) {
      if (ingredient.formulation_name) {
        result += ` ${ingredient.formulation_name}`
      }
      if (ingredient.strength) {
        result += ` (${ingredient.strength?.value} ${ingredient.strength?.unit_label})`
      }
    }
    return result
  }

  const displayIngredients = (pharmaProduct) => {
    let result = ''
    for (const formulation of pharmaProduct.formulations) {
      for (const ingredient of formulation.ingredients) {
        if (result !== '') {
          result += ', '
        }
        result += getIngredientName(ingredient)
      }
    }
    return result
  }

  const displayDosageForms = (pharmaProduct) => {
    return pharmaProduct.dosage_forms?.map((form) => form.term_name).join(', ')
  }

  const displayRoutesOfAdministration = (pharmaProduct) => {
    return pharmaProduct.routes_of_administration
      ?.map((route) => route.name)
      .join(', ')
  }

  return {
    getIngredientName,
    displayIngredients,
    displayDosageForms,
    displayRoutesOfAdministration,
  }
}
