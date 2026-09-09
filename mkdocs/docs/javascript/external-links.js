function externalLinks() {
    document.querySelectorAll('a[href]').forEach(function (link) {
        if (link.href.match(/^https?:\/\//)) {
            link.target = "_blank";
            link.rel = "noopener noreferrer";
        }
    });
}

if (typeof document$ !== "undefined") {
    document$.subscribe(function () {
        externalLinks();
    });
} else {
    document.addEventListener("DOMContentLoaded", externalLinks);
}