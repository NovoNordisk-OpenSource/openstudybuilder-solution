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
