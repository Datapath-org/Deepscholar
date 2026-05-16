const boton_logout = document.getElementById("logout_button");

// Uso el boton para ir a la url en el dataset
boton_logout.addEventListener("click", () => {
    const url = boton_logout.dataset.url;
    window.location.href = url;
});
