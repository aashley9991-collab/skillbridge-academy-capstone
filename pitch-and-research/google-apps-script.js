/**
 * Deploy as Web App. Set SHEET_ID and deploy with Anyone access.
 * Configure the resulting HTTPS /exec URL as GOOGLE_APPS_SCRIPT_WEBHOOK_URL
 * for the local SkillBridge server when Google Sheets sync is desired.
 */
const SHEET_ID = "YOUR_GOOGLE_SHEET_ID";

function doPost(e) {
  try {
    const body = JSON.parse(e.postData.contents);
    const summary = createSummary(body);
    const escalation = /scholar|financial aid|financial assistance|tuition assistance|tuition support/i.test(body.query || "");
    const sheet = SpreadsheetApp.openById(SHEET_ID).getSheetByName("Leads") || SpreadsheetApp.openById(SHEET_ID).insertSheet("Leads");
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(["Timestamp","Name","Email","Phone","Track","Query","AI Summary","Status","Human Follow-up"]);
    }
    sheet.appendRow([new Date(),safeCell(body.name),safeCell(body.email),safeCell(body.phone),safeCell(body.track),safeCell(body.query),safeCell(summary),escalation ? "Scholarship Escalated" : "New",escalation ? "YES" : "NO"]);
    return ContentService.createTextOutput(JSON.stringify({ok:true,summary:summary,humanEscalated:escalation}))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({ok:false,error:error.message}))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

function createSummary(body) {
  const tags = [];
  const query = (body.query || "").toLowerCase();
  if (/scholar|financial aid|financial assistance|tuition assistance|tuition support/.test(query)) tags.push("Scholarship - Human Review");
  if (/guarante|fixed.*income|monthly.*dollar|salary|earnings/.test(query)) tags.push("Compliance Clarification");
  if (body.track) tags.push(body.track);
  return tags.length ? tags.join(" | ") : "General Inquiry";
}

function safeCell(value) {
  const text = String(value || "");
  return /^[\s]*[=+\-@]/.test(text) ? "'" + text : text;
}
