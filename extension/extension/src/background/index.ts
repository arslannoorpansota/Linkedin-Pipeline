const DASHBOARD = 'dashboard.html';

async function openDashboard(): Promise<void> {
  const url = chrome.runtime.getURL(DASHBOARD);
  const existing = await chrome.tabs.query({ url });
  const tab = existing[0];
  if (tab?.id !== undefined) {
    await chrome.tabs.update(tab.id, { active: true });
    if (tab.windowId !== undefined) await chrome.windows.update(tab.windowId, { focused: true });
    return;
  }
  await chrome.tabs.create({ url });
}

chrome.action.onClicked.addListener(() => { void openDashboard(); });
