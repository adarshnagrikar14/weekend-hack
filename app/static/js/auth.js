import {
  getAuthStats,
  getCurrentUser,
  getUserHistory,
  loginUser,
  logoutUser,
  registerUser,
} from "./api.js";
import { escapeHtml } from "./format.js";
import { goToPage } from "./router.js";
import { getState, setState } from "./state.js";

const loginPage = document.querySelector("#login");
const appShell = document.querySelector(".app-shell");
const loginForm = document.querySelector("#loginForm");
const registerForm = document.querySelector("#registerForm");
const loginStatus = document.querySelector("#loginStatus");
const registerStatus = document.querySelector("#registerStatus");
const userBadge = document.querySelector("#userBadge");
const logoutBtn = document.querySelector("#logoutBtn");
const historyList = document.querySelector("#userHistory");
const statsBox = document.querySelector("#statsBox");

export async function initAuth() {
  loginForm.addEventListener("submit", handleLogin);
  registerForm.addEventListener("submit", handleRegister);
  logoutBtn.addEventListener("click", handleLogout);
  window.addEventListener("auth:expired", () => {
    loginStatus.textContent = "Session expired. Please sign in again.";
    setLoggedOutState();
  });

  const token = localStorage.getItem("orchestrateai_token");
  if (!token) {
    setLoggedOutState();
    return false;
  }
  try {
    const { user } = await getCurrentUser();
    setState({ user });
    setLoggedInState(user);
    await Promise.all([loadHistory(), loadStats()]);
    return true;
  } catch {
    setLoggedOutState();
    return false;
  }
}

function setLoggedOutState() {
  localStorage.removeItem("orchestrateai_token");
  setState({ user: null });
  appShell.classList.add("is-logged-out");
  goToPage("login");
}

function setLoggedInState(user) {
  appShell.classList.remove("is-logged-out");
  userBadge.textContent = `${user.display_name} (${user.role})`;
  goToPage("intake");
}

async function handleLogin(event) {
  event.preventDefault();
  loginStatus.textContent = "Signing in...";
  const payload = Object.fromEntries(new FormData(loginForm).entries());
  try {
    const result = await loginUser(payload);
    localStorage.setItem("orchestrateai_token", result.access_token);
    setState({ user: result.user });
    setLoggedInState(result.user);
    loginStatus.textContent = "Signed in.";
    await Promise.all([loadHistory(), loadStats()]);
  } catch (error) {
    loginStatus.textContent = error.message;
  }
}

async function handleRegister(event) {
  event.preventDefault();
  registerStatus.textContent = "Creating account...";
  const payload = Object.fromEntries(new FormData(registerForm).entries());
  try {
    await registerUser(payload);
    registerStatus.textContent = "Account created. Redirecting to sign in...";
    registerForm.reset();
    setTimeout(() => goToPage("login"), 700);
  } catch (error) {
    registerStatus.textContent = error.message;
  }
}

async function handleLogout() {
  try {
    if (getState().user) await logoutUser();
  } finally {
    setLoggedOutState();
  }
}

async function loadHistory() {
  try {
    const { events } = await getUserHistory();
    historyList.innerHTML = events.length
      ? events
          .slice(0, 8)
          .map(
            (event) =>
              `<li><strong>${escapeHtml(event.event_type)}</strong><span>${escapeHtml(event.summary)}</span></li>`
          )
          .join("")
      : "<li><span>No user history yet.</span></li>";
  } catch {
    historyList.innerHTML = "<li><span>History unavailable for this role.</span></li>";
  }
}

async function loadStats() {
  try {
    const stats = await getAuthStats();
    statsBox.innerHTML = `
      <div><strong>Users</strong><span>${Object.values(stats.users_by_role || {}).reduce((a, b) => a + b, 0)}</span></div>
      <div><strong>Auth events (24h)</strong><span>${stats.auth_events_24h}</span></div>
      <div><strong>Total demands</strong><span>${stats.demands_total}</span></div>
      <div><strong>Activity entries</strong><span>${stats.activity_total}</span></div>
    `;
  } catch {
    statsBox.innerHTML = "<div><strong>Stats</strong><span>Restricted by role</span></div>";
  }
}
