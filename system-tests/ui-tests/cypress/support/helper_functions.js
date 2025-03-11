export function stringToBoolean(value) {
  switch (value) {
    case true:
      return "Yes";
    case false:
      return "No";
    case null:
      return "";
  }
}

export function getCurrStudyUid() {
  let curr_study = JSON.parse(window.localStorage.getItem("selectedStudy"));
  return curr_study.uid;
}

export function getCurrentDateFormatted() {
  const currentDate = new Date();

  const options = {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "numeric",
    hour12: true,
  };

  const formattedDate = currentDate.toLocaleString("en-US", options);

  return formattedDate;
}

export function formatDateToMMMDDYYYY() {
  return new Date().toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });
}

export function getUidByStudyId(chosen_study_id, dataset) {
    for (const item of dataset) {
      const studyId = item.current_metadata.identification_metadata.study_id;
      if (studyId === chosen_study_id) {
        return item.uid;
      }
    }
    return null; // Return null if no matching study_id is found
}

export function getCurrentDateYYYYMMDD() {
  return new Date().toISOString().split('T')[0];
}


export function findMetadataByVersionAndStatus(
  dataset,
  versionNumber,
  studyStatus
) {
  console.log(dataset)
    // Iterate through the items in the dataset
    for (const item of dataset) {
      if (
        item.current_metadata.version_metadata.version_number ===
        versionNumber &&
        item.current_metadata.version_metadata.study_status === studyStatus
      ) {
        console.log(item)
        return item; // Return the item that matches the criteria
      }
    }

    // If no matching item is found, return null or handle it as needed
    return null;
}

export function currentDate() {
  return new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}