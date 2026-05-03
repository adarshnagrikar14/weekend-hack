import { initIntake } from "./intake.js";
import { renderPipeline } from "./pipeline.js";
import { initRouter } from "./router.js";
import { initVoiceExplainability } from "./voice.js";

async function boot() {
  initRouter();
  document.addEventListener("pipeline:updated", (event) => {
    renderPipeline(event.detail);
  });
  await initIntake();
  initVoiceExplainability();
}

boot().catch((error) => {
  const status = document.querySelector("#demandStatus");
  if (status) {
    status.textContent = error.message;
  }
});
