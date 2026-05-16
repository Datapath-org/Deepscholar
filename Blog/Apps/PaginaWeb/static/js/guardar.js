document.addEventListener("click", (event) => {
    if(event.target.classList.contains("save_button")) {
        const url = event.target.dataset.url;
        fetch(url);
    }
});