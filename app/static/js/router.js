const pages = [...document.querySelectorAll("[data-page]")];
const links = [...document.querySelectorAll("[data-page-link]")];

const defaultPage = "intake";

export function initRouter() {
  window.addEventListener("hashchange", showCurrentPage);
  showCurrentPage();
}

export function goToPage(page) {
  window.location.hash = page;
}

function showCurrentPage() {
  const requested = window.location.hash.replace("#", "") || defaultPage;
  const activePage = pages.some((page) => page.dataset.page === requested) ? requested : defaultPage;

  pages.forEach((page) => {
    page.hidden = page.dataset.page !== activePage;
  });

  links.forEach((link) => {
    link.classList.toggle("active", link.dataset.pageLink === activePage);
  });
}
