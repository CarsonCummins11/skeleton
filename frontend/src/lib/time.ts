export function timestamp_to_human_readable(usec: number): string {
  const date = new Date(usec / 1000); // Convert microseconds to milliseconds

  const now = new Date();
  const isCurrentYear = date.getFullYear() === now.getFullYear();

  const monthNames = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ];
  const month = monthNames[date.getMonth()];
  const day = date.getDate();

  let hours = date.getHours();
  const minutes = date.getMinutes();
  const ampm = hours >= 12 ? "pm" : "am";
  hours = hours % 12 || 12; // Convert to 12-hour format

  const minutesStr = minutes.toString().padStart(2, "0");

  const timePart = `${hours}:${minutesStr}${ampm}`;
  if (isCurrentYear) {
    return `${month} ${day}, ${timePart}`;
  } else {
    return `${month} ${day} ${date.getFullYear()}, ${timePart}`;
  }
}
