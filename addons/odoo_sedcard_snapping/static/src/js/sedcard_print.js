/** @odoo-module **/

function enableSedcardPrintLayout() {
    if (!document.querySelector(".s_sedcard")) {
        return;
    }
    document.documentElement.classList.add("o_sedcard_print_layout");
    if (document.head.querySelector("style[data-sedcard-page]")) {
        return;
    }
    const pageStyle = document.createElement("style");
    pageStyle.dataset.sedcardPage = "true";
    pageStyle.media = "print";
    pageStyle.textContent = "@page { size: A4 portrait; margin: 0; }";
    document.head.appendChild(pageStyle);
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", enableSedcardPrintLayout, { once: true });
} else {
    enableSedcardPrintLayout();
}
