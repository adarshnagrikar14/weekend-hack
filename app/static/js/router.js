const pages = [...document.querySelectorAll("[data-page]")];
const links = [...document.querySelectorAll("[data-page-link]")];

export function initRouter() {
  window.addEventListener("hashchange", showCurrentPage);
  showCurrentPage();
}

export function goToPage(page) {
  window.location.hash = page;
}

function showCurrentPage() {
  const hasToken = Boolean(localStorage.getItem("orchestrateai_token"));
  const fallback = hasToken ? "intake" : "login";
  const requested = window.location.hash.replace("#", "") || fallback;
  const publicPages = new Set(["login", "signup"]);
  const safeRequested = !hasToken && !publicPages.has(requested) ? "login" : requested;
  const activePage = pages.some((page) => page.dataset.page === safeRequested) ? safeRequested : fallback;

  pages.forEach((page) => {
    page.hidden = page.dataset.page !== activePage;
  });

  links.forEach((link) => {
    link.classList.toggle("active", link.dataset.pageLink === activePage);
  });
}
