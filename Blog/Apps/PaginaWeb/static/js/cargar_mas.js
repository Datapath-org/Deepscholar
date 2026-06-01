let page = 1;

// Reconoce boton para cargar mas
const boton_more = document.getElementById("more_button");

boton_more.addEventListener("click", async () => {
    page++;

    // Cambia el valor de page en la url para que luego
    // en views se obtenga el valor
    const response = await fetch(`/more/?page=${page}`);

    // Carga los articulos obtenidos en views
    const data = await response.json();

    // Encuentra el contenedor para los articulos
    const contenedor = document.getElementById("cont_art");

    data.docs.forEach(doc => {
        const list = document.createElement("li");

        list.innerHTML = 
            `<p><strong>Bibcode:</strong> ${doc.bibcode}</p>
             <p><strong>Titulo:</strong> ${doc.title[0]}</p>
             <p><strong>Autores:</strong> ${formatAuthors(doc.author)}</p>
             <p><strong>Resumen:</strong> ${doc.abstract}</p>
             <p><strong>Fecha:</strong> ${doc.pubdate}</p>
             <p><strong>No. de citas:</strong> ${doc.citation_count}</p>

             <div style="text-align: right;">
             ${doc.liked
                ? `<button class="delete_button" data-url="/delete/${doc.bibcode}/">
                        Borrar
                    </button>`
                : `<button class="save_button" data-url="/save/${doc.bibcode}/">
                        Guardar
                   </button>`
             }
             </div>
             <hr>`;

        contenedor.appendChild(list);
    });
});
