document.addEventListener("DOMContentLoaded", function (event) {
    document.querySelectorAll("a").forEach((anchor) => {
        anchor.addEventListener("click", (e) => {
            parent.postMessage(
                JSON.stringify({ "url": e.target.href }),
                document.location.origin
            );
            e.preventDefault();
            e.stopPropagation();
        });
    });
});