export function useActivities() {
  const displayActivityGroups = (activity) => {
    return activity.activity_groupings
      .map((element) => `&#9679; ${element.activity_group_name}`)
      .join('<br/>')
  }

  const displayActivitySubgroups = (activity) => {
    return activity.activity_groupings
      .map((element) => `&#9679; ${element.activity_subgroup_name}`)
      .join('<br/>')
  }

  return { displayActivityGroups, displayActivitySubgroups }
}
