(() => {
  const rows = [["Title", "Link", "Signatures"]];
  
  // Target the petition entries on the page
  document.querySelectorAll('li.petResult').forEach(item => {
    const titleLink = item.querySelector('.title a');
    if (!titleLink) return;
    
    // Format Title and Link
    const title = titleLink.innerText.trim().replace(/\s+/g, ' ').replace(/"/g, '""');
    const href = titleLink.getAttribute('href');
    const fullLink = href.startsWith('http') ? href : `https://peticaopublica.com${href}`;
    
    // Extract Signature Count
    const sigText = item.querySelector('.body p:last-child')?.innerText || "N/A";
    const sigMatch = sigText.match(/\d+/);
    const signatures = sigMatch ? sigMatch[0] : "0";

    rows.push([`"${title}"`, `"${fullLink}"`, `"${signatures}"`]);
  });

  if (rows.length <= 1) {
    console.error("No petResult items found on this page.");
    return;
  }

  // Convert to CSV text format
  const csvText = rows.map(e => e.join(",")).join("\n");

  // Copy directly to system clipboard
  copy(csvText);

  const pgMatch = window.location.href.match(/pg=(\d+)/);
  const pageNum = pgMatch ? pgMatch[1] : "1";

  console.log(`%c Success! Extracted ${rows.length - 1} items from Page ${pageNum} and copied to clipboard!`, 'color: #00ff00; font-weight: bold;');
  console.log("Press Ctrl+V (or Cmd+V) in Excel, Google Sheets, or Notepad to paste.");
})();