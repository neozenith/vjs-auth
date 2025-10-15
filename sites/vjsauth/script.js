/**
 * VJS Auth - Main JavaScript
 *
 * This script dynamically updates the page to demonstrate successful loading.
 */

(function () {
  "use strict";

  // Log initialization
  console.log("VJS Auth script.js loaded successfully");
  console.log("Port: 5173");
  console.log("Ready for iterative development");

  /**
   * Initialize the application when DOM is ready
   */
  function init() {
    console.log("Initializing VJS Auth...");

    // Update status indicator
    updateStatusIndicator();

    // Add dynamic timestamp
    addTimestamp();

    // Add interactive features
    addInteractiveFeatures();

    console.log("VJS Auth initialized successfully");
  }

  /**
   * Update the status indicator to show script loaded
   */
  function updateStatusIndicator() {
    const statusContainer = document.getElementById("status-container");
    if (!statusContainer) return;

    // Create new status item
    const statusItem = document.createElement("li");
    statusItem.className = "animate-fade-in";
    statusItem.innerHTML = "✓ JavaScript loaded and executed";

    statusContainer.appendChild(statusItem);
  }

  /**
   * Add timestamp to show when script executed
   */
  function addTimestamp() {
    const timestampContainer = document.getElementById("timestamp");
    if (!timestampContainer) return;

    const now = new Date();
    const timeString = now.toLocaleTimeString();
    const dateString = now.toLocaleDateString();

    timestampContainer.innerHTML = `
            <div class="text-sm text-gray-600 mt-4 p-3 bg-gray-50 rounded-lg">
                <strong>Script executed:</strong> ${dateString} at ${timeString}
            </div>
        `;
  }

  /**
   * Add interactive features to demonstrate dynamic capabilities
   */
  function addInteractiveFeatures() {
    // Add click counter to demonstrate interactivity
    const container = document.querySelector(".container");
    if (!container) return;

    let clickCount = 0;

    const clickCounter = document.createElement("div");
    clickCounter.id = "click-counter";
    clickCounter.className = "mt-6 p-4 bg-indigo-50 rounded-lg border-l-4 border-indigo-500";
    clickCounter.innerHTML = `
            <h3 class="text-indigo-700 font-semibold mb-2">Interactive Demo</h3>
            <p class="text-gray-700 mb-3">Click the button to test dynamic updates:</p>
            <button
                id="demo-button"
                class="bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200"
            >
                Click Me! (Count: <span id="click-count">0</span>)
            </button>
        `;

    container.appendChild(clickCounter);

    // Add click handler
    const demoButton = document.getElementById("demo-button");
    const clickCountSpan = document.getElementById("click-count");

    if (demoButton && clickCountSpan) {
      demoButton.addEventListener("click", function () {
        clickCount++;
        clickCountSpan.textContent = clickCount;
        console.log(`Button clicked ${clickCount} time(s)`);

        // Add visual feedback
        this.classList.add("scale-95");
        setTimeout(() => {
          this.classList.remove("scale-95");
        }, 100);
      });
    }
  }

  /**
   * Wait for DOM to be ready, then initialize
   */
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    // DOM is already ready
    init();
  }
})();
