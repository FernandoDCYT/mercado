// Seleccionar elementos
const menuLateral = document.getElementById("menu-lateral");
const toggleMenuBoton = document.getElementById("toggle-menu");
const contenidoPrincipal = document.querySelector(".contenido-principal");
const buscador = document.getElementById("buscador");
const toggleVistaBoton = document.getElementById("toggle-vista");
const gestionProductos = document.querySelector(".gestion-productos");
const listaProductos = document.querySelector(".lista-productos");
const buscadorVentas = document.getElementById("buscador-ventas");
const resultadosBusqueda = document.getElementById("resultados-busqueda");
const productoIdInput = document.getElementById("producto_id");

let vistaActual = "cuadrados";
let productos = [];

// Función para alternar el menú
function toggleMenu() {
    menuLateral.classList.toggle("visible");
    contenidoPrincipal.classList.toggle("menu-abierto");
}

// Agregar evento al botón del menú
toggleMenuBoton.addEventListener("click", toggleMenu);

// Función para filtrar productos
function filtrarProductos(texto) {
    const productosCuadrados = document.querySelectorAll(".caja-producto");
    productosCuadrados.forEach(producto => {
        const nombre = producto.querySelector("span").textContent.toLowerCase();
        if (nombre.includes(texto.toLowerCase())) {
            producto.style.display = "block";
        } else {
            producto.style.display = "none";
        }
    });

    const productosLista = document.querySelectorAll(".lista-item");
    productosLista.forEach(producto => {
        const nombre = producto.querySelector(".nombre-producto").textContent.toLowerCase();
        if (nombre.includes(texto.toLowerCase())) {
            producto.style.display = "flex";
        } else {
            producto.style.display = "none";
        }
    });
}

// Agregar evento al buscador
buscador.addEventListener("input", function() {
    filtrarProductos(this.value);
});

// Función para cambiar la vista
function cambiarVista() {
    if (vistaActual === "cuadrados") {
        gestionProductos.style.display = "none";
        listaProductos.style.display = "block";
        toggleVistaBoton.textContent = "Vista: Lista";
        vistaActual = "lista";
    } else {
        gestionProductos.style.display = "flex";
        listaProductos.style.display = "none";
        toggleVistaBoton.textContent = "Vista: Cuadrados";
        vistaActual = "cuadrados";
    }
}

// Agregar evento al botón de vista
toggleVistaBoton.addEventListener("click", cambiarVista);

// Calcular y mostrar el precio con IVA en la vista de lista
function calcularPrecioConIVA() {
    const productosLista = document.querySelectorAll(".lista-item");
    productosLista.forEach(producto => {
        const precio = parseFloat(producto.dataset.precio);
        const precioConIVA = precio * 1.16;
        producto.querySelector(".precio-producto").textContent = "$" + precioConIVA.toFixed(2);
    });
}

// Llamar a la función calcularPrecioConIVA al cargar la página
window.addEventListener("load", calcularPrecioConIVA);

// Función para buscar productos en la página de ventas
function buscarProductosVentas(texto) {
    resultadosBusqueda.innerHTML = "";
    resultadosBusqueda.style.display = "none";

    if (texto.length < 3) {
        return;
    }

    const resultados = productos.filter(producto =>
        producto.p_nom.toLowerCase().includes(texto.toLowerCase())
    );

    if (resultados.length > 0) {
        resultadosBusqueda.style.display = "block";
        resultados.forEach(producto => {
            const a = document.createElement("a");
            a.innerHTML = resaltarTexto(producto.p_nom, texto); // Usar la función para resaltar
            a.href = "#";
            a.addEventListener("click", function(event) {
                event.preventDefault();
                buscadorVentas.value = producto.p_nom;
                productoIdInput.value = producto.p_id_producto;
                resultadosBusqueda.style.display = "none";
            });
            resultadosBusqueda.appendChild(a);
        });
    }
}

// Función para resaltar el texto buscado en los resultados
function resaltarTexto(texto, busqueda) {
    const regex = new RegExp(busqueda, 'gi');
    return texto.replace(regex, '<span class="resaltar">$&</span>');
}

// Agregar evento al buscador de ventas
buscadorVentas.addEventListener("input", function() {
    buscarProductosVentas(this.value);
});

// Obtener la lista de productos desde el servidor
async function obtenerProductos() {
    try {
        const response = await fetch("/productos");
        productos = await response.json();
    } catch (error) {
        console.error("Error al obtener los productos:", error);
    }
}

// Llamar a la función obtenerProductos al cargar la página
window.addEventListener("load", obtenerProductos);