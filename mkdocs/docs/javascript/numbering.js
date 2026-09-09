function numberHeadings() {
    const content = document.querySelector(".md-content");

    if (!content) {
        return;
    }

    /*
     * Remove numbers from a previous run.
     * This is important when Material uses instant navigation.
     */
    content.querySelectorAll(".heading-number").forEach((element) => {
        element.remove();
    });

    document.querySelectorAll(".md-nav--secondary .heading-number").forEach((element) => {
        element.remove();
    });

    /*
     * Counters for H1 ... H6
     */
    const counters = [0, 0, 0, 0, 0, 0];

    /*
     * Store the generated number for every heading ID.
     * This allows us to use exactly the same number in the TOC.
     */
    const headingNumbers = new Map();

    /*
     * Number all headings in the page content.
     */
    content.querySelectorAll("h1, h2, h3, h4, h5, h6").forEach((heading) => {
        const level = Number(heading.tagName.substring(1));

        counters[level - 1]++;

        // Reset all deeper levels.
        for (let i = level; i < counters.length; i++) {
            counters[i] = 0;
        }

        const number = counters
            .slice(0, level)
            .join(".");

        headingNumbers.set(heading.id, number);

        const span = document.createElement("span");
        span.className = "heading-number";
        span.textContent = `${number}. `;

        heading.prepend(span);
    });

    /*
     * Number the right-hand table of contents.
     *
     * We identify TOC entries by their href and match them
     * against the ID of the corresponding heading.
     */
    document
        .querySelectorAll(".md-nav--secondary a.md-nav__link")
        .forEach((link) => {
            const url = new URL(link.href, window.location.href);
            const headingId = decodeURIComponent(url.hash.substring(1));

            const number = headingNumbers.get(headingId);

            if (!number) {
                return;
            }

            const span = document.createElement("span");
            span.className = "heading-number";
            span.textContent = `${number}. `;

            link.prepend(span);
        });
}


/*
 * Material for MkDocs exposes document$.
 *
 * This is preferable to DOMContentLoaded because it also runs
 * after Material's instant navigation has replaced the page.
 */
if (typeof document$ !== "undefined") {
    document$.subscribe(() => {
        numberHeadings();
    });
} else {
    document.addEventListener("DOMContentLoaded", () => {
        numberHeadings();
    });
}