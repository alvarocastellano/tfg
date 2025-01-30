function main() {
    // We now establish the core components: scene, renderer, and camera.
    const scene = new THREE.Scene();
    const renderer = new THREE.WebGLRenderer({ canvas: document.querySelector('#globe') });
    renderer.setSize(window.innerWidth, window.innerHeight);
    const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 1.7;

    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();


    const markers = [
        { lat: 50.8503, lng: 4.3517, cities: ['Bruselas'], country: 'Belgica', flag: 'belgica.png' },
        { lat: 42.6977, lng: 23.3219, cities: ['Sofia'], country: 'Bulgaria', flag: 'bulgaria.png' },
        { lat: 50.0755, lng: 14.4378, cities: ['Praga'], country: 'Chequia', flag: 'chequia.png' },
        { lat: 55.6761, lng: 12.5683, cities: ['Copenhague'], country: 'Dinamarca', flag: 'dinamarca.png' },
        { lat: 52.5200, lng: 13.4050, cities: ['Berlin','Munich'], country: 'Alemania', flag: 'alemania.png' },
        { lat: 59.4370, lng: 24.7536, cities: ['Tallinn'], country: 'Estonia', flag: 'estonia.png' },
        { lat: 53.3498, lng: -6.2603, cities: ['Dublin','Cork'], country: 'Irlanda', flag: 'irlanda.png' },
        { lat: 37.9838, lng: 23.7275, cities: ['Atenas'], country: 'Grecia', flag: 'grecia.png' },
        { lat: 40.4168, lng: -3.7038, cities: ['Madrid','Sevilla','Barcelona'], country: 'España', flag: 'spain.png' },
        { lat: 48.8566, lng: 2.3522, cities: ['Paris','Lens','Marsella'], country: 'Francia', flag: 'francia.png' },
        { lat: 45.8150, lng: 15.9819, cities: ['Zagreb','Split'], country: 'Croacia', flag: 'croacia.png' },
        { lat: 41.9028, lng: 12.4964, cities: ['Roma','Salerno','Florencia','Bari'], country: 'Italia', flag: 'italia.png' },
        { lat: 49.6116, lng: 6.1319, cities: ['Luxemburgo'], country: 'Luxemburgo', flag: 'luxemburgo.png' },
        { lat: 47.4979, lng: 19.0402, cities: ['Budapest'], country: 'Hungría', flag: 'hungria.png' },
        { lat: 35.8989, lng: 14.5146, cities: ['La Valeta'], country: 'Malta', flag: 'malta.png' },
        { lat: 52.3676, lng: 4.9041, cities: ['Amsterdam','Roterdam'], country: 'Países Bajos', flag: 'holanda.png' },
        { lat: 48.2082, lng: 16.3738, cities: ['Viena'], country: 'Austria', flag: 'austria.png' },
        { lat: 52.2297, lng: 21.0122, cities: ['Varsovia'], country: 'Polonia', flag: 'polonia.png' },
        { lat: 38.7167, lng: -9.1333, cities: ['Lisboa','Oporto'], country: 'Portugal', flag: 'portugal.png' },
        { lat: -34.6037, lng: -58.3816, cities: ['Buenos Aires'], country: 'Argentina', flag: 'argentina.png' },
        { lat: -35.2809, lng: 149.1300, cities: ['Canberra'], country: 'Australia', flag: 'australia.png' },
        { lat: -15.7801, lng: -47.9292, cities: ['Brasilia'], country: 'Brasil', flag: 'brasil.png' },
        { lat: 45.4215, lng: -75.6972, cities: ['Ottawa'], country: 'Canadá', flag: 'canada.png' },
        { lat: -33.4489, lng: -70.6693, cities: ['Santiago'], country: 'Chile', flag: 'chile.png' },
        { lat: 39.9042, lng: 116.4074, cities: ['Pekín'], country: 'China', flag: 'china.png' },
        { lat: 38.9072, lng: -77.0369, cities: ['Washington D.C.'], country: 'Estados Unidos', flag: 'estados_unidos.png' },
        { lat: 28.6139, lng: 77.2090, cities: ['Nueva Delhi'], country: 'India', flag: 'india.png' },
        { lat: 35.6762, lng: 139.6503, cities: ['Tokio'], country: 'Japón', flag: 'japon.png' },
        { lat: -34.9011, lng: -56.1645, cities: ['Montevideo'], country: 'Uruguay', flag: 'uruguay.png' },
    ];

    const suggestionsDiv = document.getElementById("suggestions");


    document.getElementById("citySearch").addEventListener("input", function() {
        const searchValue = this.value.toLowerCase();
        
        // Limpia las sugerencias previas
        suggestionsDiv.innerHTML = '';

        // Si no hay entrada o es menor que 1 caracter, no mostramos sugerencias
        if (searchValue.length < 1) {
            suggestionsDiv.style.display = 'none';
            return;
        }

        // Filtra las ciudades que coinciden con la búsqueda
        const filteredMarkers = markers.filter(marker => 
            marker.cities.some(city => city.toLowerCase().startsWith(searchValue))
        );

        if (filteredMarkers.length > 0) {
            filteredMarkers.forEach(marker => {
                marker.cities.forEach(city => {
                    if (city.toLowerCase().startsWith(searchValue)) {
                        const suggestion = document.createElement("div");
                        suggestion.textContent = city; // Muestra el nombre de la ciudad
                        suggestion.addEventListener("click", () => {
                            document.getElementById("citySearch").value = city; // Completa el input con la ciudad
                            suggestionsDiv.style.display = 'none'; // Oculta las sugerencias
                        });
                        suggestionsDiv.appendChild(suggestion);
                    }
                });
            });
            suggestionsDiv.style.display = 'block'; // Muestra las sugerencias
        } else {
            suggestionsDiv.style.display = 'none'; // Oculta las sugerencias si no hay resultados
        }
    });

    document.getElementById("searchBtn").addEventListener("click", () => {
        const searchValue = document.getElementById("citySearch").value.toLowerCase();
        const marker = markers.find(m =>
            m.cities.some(city => city.toLowerCase() === searchValue) ||
            m.country.toLowerCase() === searchValue
        );

        if (marker) {
            // Encontrar la ciudad exacta dentro del marker
            const city = marker.cities.find(city => city.toLowerCase() === searchValue) || marker.cities[0];
            
            fetch(updateCityURL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({ selected_city: city })
            })
            .then(response => {
                if (response.ok) {
                    return response.json();
                } else {
                    return response.json().then(errorData => { throw new Error(errorData.message || 'Error desconocido'); });
                }
            })
            .then(data => {
                if (data.success) {
                    // Muestra el modal con los datos de la ciudad
                    document.getElementById("cityModalLabel").innerHTML = `
                        <div style="display: flex; align-items: center; justify-content: center;">
                            <span style="margin-right: 10px;">${city}, ${marker.country}</span>
                            <img src="/static/images/${marker.flag}" alt="${marker.country} flag" style="width: 30px; height: auto;">
                        </div>
                    `;

                    // Actualizar el enlace de Mercado
                    const marketButton = document.getElementById("marketButton");
                    marketButton.href = `/marketplace/market/products/city=${city}`;

                    const communityButton = document.getElementById("communityButton");
                    communityButton.href = `/community/chat/${city}`;

                    const eventsButton = document.getElementById("eventsButton");
                    eventsButton.href = `/events/calendar/city=${city}`;

                    const turismButton = document.getElementById("turismButton");
                    turismButton.href = `/turism/city_map/${city}`;


                    $('#cityModal').modal('show');
                } else {
                    showError(data.message);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showError(error.message);
            });
        } else {
            alert("La ciudad buscada no está en Worldin");
        }
    });

    // Función para mostrar el mensaje de error
    function showError(message) {
        const errorMessageContainer = document.getElementById('errorMessageContainer');
        const errorText = document.getElementById('errorText');
        
        // Coloca el mensaje de error en el contenedor
        errorText.innerHTML = message;
        
        // Muestra el contenedor
        errorMessageContainer.style.display = 'block';
    }
    
    

    // Let's get into the Earth itself.

    const map = '/static/images/earthmap.jpeg';
    const bumpMap = '/static/images/earthbump.jpeg';

    const earthGeometry = new THREE.SphereGeometry(0.5, 32, 32);
    const earthMaterial = new THREE.MeshPhongMaterial({
        map: new THREE.TextureLoader().load(map),
        bumpMap: new THREE.TextureLoader().load(bumpMap),
        bumpScale: 0.01,
    });
    const earthMesh = new THREE.Mesh(earthGeometry, earthMaterial);
    scene.add(earthMesh);

    // Let's light up our globe by adding some lighting effects.
    const pointLight = new THREE.PointLight(0xffffff, 1.05, 3.5, 0);
    pointLight.position.set(0.1, 0.1, 3);
    scene.add(pointLight);

    // Let’s make our globe more realistic by adding clouds.
    const earthCloud = '/static/images/earthCloud.png';
    const cloudGeometry = new THREE.SphereGeometry(0.51, 32, 32);
    const cloudMaterial = new THREE.MeshPhongMaterial({
        map: new THREE.TextureLoader().load(earthCloud),
        transparent: true
    });
    const cloudMesh = new THREE.Mesh(cloudGeometry, cloudMaterial);
    scene.add(cloudMesh);

    // Create a ring for the atmosphere effect
    //const atmosphereGeometry = new THREE.RingGeometry(0.54, 0.535, 32); // Create a ring
    //const atmosphereMaterial = new THREE.MeshBasicMaterial({
        //color: 0x1E90FF, // Blue color for the atmosphere
        //transparent: true,
        //opacity: 0.2,
        //side: THREE.DoubleSide // Make the ring visible from both sides
    //});
    //const atmosphereMesh = new THREE.Mesh(atmosphereGeometry, atmosphereMaterial);
    //scene.add(atmosphereMesh);

    // To create a celestial atmosphere, we will introduce a star-ry background texture.
    const galaxy = '/static/images/galaxy.png';
    const backgroundLoader = new THREE.TextureLoader();

    // Cargar la textura de la galaxia y asignarla como fondo de la escena
    backgroundLoader.load(galaxy, function(texture) {
        scene.background = texture; // Asignar la textura al fondo de la escena
    });

    // Declare and initialize variables for interaction and rotation.
    let targetRotationX = 0.0005;
    let targetRotationY = 0.00;
    let mouseX = 0, mouseXOnMouseDown = 0, mouseY = 0, mouseYOnMouseDown = 0;
    const windowHalfX = window.innerWidth / 2;
    const windowHalfY = window.innerHeight / 2;
    const dragFactor = 0.00005;

    //marcadores
    // Step 1: Crear la función para convertir lat/lng a Vector3
    function latLngToVector3(lat, lng, radius) {
        const phi = (90 - lat) * (Math.PI / 180);
        const theta = (lng + 180) * (Math.PI / 180);
        
        const x = -(radius * Math.sin(phi) * Math.cos(theta));
        const y = radius * Math.cos(phi);
        const z = radius * Math.sin(phi) * Math.sin(theta);
        
        return new THREE.Vector3(x, y, z);
    }

    //Añadir marcadores a la escena
    const placeMarker = '/static/images/marker.png';
    const markerMaterial = new THREE.SpriteMaterial({ 
        map: new THREE.TextureLoader().load(placeMarker), // Ruta a tu imagen del marcador
        color: 0xffffff
    });

    // Mantén un array para almacenar los sprites de los marcadores
    const markersSprites = [];

    // Inicializa el tamaño del renderizador
    renderer.setSize(window.innerWidth, window.innerHeight);
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();

    function onWindowResize() {
        renderer.setSize(window.innerWidth, window.innerHeight); // Ajustar el tamaño del renderizador
        camera.aspect = window.innerWidth / window.innerHeight; // Actualizar el aspecto de la cámara
        camera.updateProjectionMatrix(); // Actualizar la matriz de proyección
    }

    // Añade el manejador de eventos para el redimensionamiento de la ventana
    window.addEventListener('resize', onWindowResize, false);    
    
    // Coloca los marcadores como hijos de earthMesh para que se sincronicen con la rotación de la Tierra
    markers.forEach(marker => {
        const { lat, lng, cities, country, flag } = marker;
        const position = latLngToVector3(lat, lng, 0.515); // Ajusta el radio según tu esfera
        const sprite = new THREE.Sprite(markerMaterial);
        sprite.position.copy(position);
        sprite.scale.set(0.03, 0.03, 1); // Ajusta el tamaño del marcador
        sprite.userData = { cities, country, flag };
        earthMesh.add(sprite); // Añadir el marcador como hijo de la Tierra
        markersSprites.push(sprite); // Almacenar el sprite en el array
    });
    

    

    // Hide the spinner when the textures are loaded
    const textureLoader = new THREE.TextureLoader();
    let texturesLoaded = 0;
    const totalTextures = 3; // earthmap, bumpMap, earthCloud

    const onTextureLoad = () => {
        texturesLoaded++;
        if (texturesLoaded === totalTextures) {
            document.getElementById('spinner').style.display = 'none'; // Hide the spinner
        }
    };

    // Load textures
    textureLoader.load(map, onTextureLoad);
    textureLoader.load(bumpMap, onTextureLoad);
    textureLoader.load(earthCloud, onTextureLoad);
    
    // Define functions that handle mouse events for interaction with the Globe.
    let rotationSpeedX = 0;
    let rotationSpeedY = 0;
    let isDragging = false; // Variable para comprobar si el ratón está siendo arrastrado
    const dampingFactor = 0.9; // Factor de amortiguación para que se suavice
    const stopThreshold = 0.0001; // Umbral para detener la rotación

    function onDocumentMouseDown(event) {
        event.preventDefault();
        // Calcula la posición del clic del ratón en el espacio de coordenadas normalizadas
        mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
        mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

        // Utiliza el raycaster para detectar intersecciones con earthMesh
        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObject(earthMesh);

        // Si el clic es sobre la esfera, habilita el arrastre
        if (intersects.length > 0) {
            document.addEventListener('mousemove', onDocumentMouseMove, false);
            document.addEventListener('mouseup', onDocumentMouseUp, false);
            mouseXOnMouseDown = event.clientX;
            mouseYOnMouseDown = event.clientY;
            isDragging = true;
        }
    }

    const inputElement = document.getElementById('citySearch');
        inputElement.addEventListener('mousedown', function(event) {
            event.stopPropagation(); // Detiene la propagación del evento al documento
        });

    function onDocumentMouseDown2(event) {
        event.preventDefault();
        
        // Configurar las coordenadas del ratón para el raycaster
        mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
        mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;
        
        raycaster.setFromCamera(mouse, camera);
        
        // Verificar la intersección con los marcadores
        const intersects = raycaster.intersectObjects(markersSprites);
        const intersectsEarth = raycaster.intersectObject(earthMesh);
    
        if (intersectsEarth.length > 0) {
            if (intersects.length > 0) {
                const marker = intersects[0].object;
                const { cities, country, flag } = marker.userData;
                const city = cities[0]; // Selecciona la primera ciudad del marcador

                // Actualiza la ciudad seleccionada en el servidor
                fetch(updateCityURL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({ selected_city: city })
                })
                .then(response => {
                    if (response.ok) {
                        return response.json();
                    } else {
                        return response.json().then(errorData => { throw new Error(errorData.message || 'Error desconocido'); });
                    }
                })
                .then(data => {
                    if (data.success) {
                        // Muestra el modal con los datos del marcador
                        document.getElementById("cityModalLabel").innerHTML = `
                            <div style="display: flex; align-items: center; justify-content: center;">
                                <span style="margin-right: 10px;">${city}, ${country}</span>
                                <img src="/static/images/${flag}" alt="${country} flag" style="width: 30px; height: auto;">
                            </div>
                        `;
                        // Actualizar el enlace de Mercado
                        const marketButton = document.getElementById("marketButton");
                        marketButton.href = `/marketplace/market/products/city=${city}`;

                        const communityButton = document.getElementById("communityButton");
                        communityButton.href = `/community/chat/${city}`;

                        const eventsButton = document.getElementById("eventsButton");
                        eventsButton.href = `/events/calendar/city=${city}`;

                        const turismButton = document.getElementById("turismButton");
                        turismButton.href = `/turism/city_map/${city}`;

                        // Muestra el modal
                        $('#cityModal').modal('show');
                    } else {
                        showError(data.message);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    showError(error.message);
                });
            } else {
                console.log("No marker intersection detected.");
            }
        }
    }
    
    window.addEventListener('mousedown', onDocumentMouseDown2);
    

    function onDocumentMouseMove(event) {
        if (isDragging) {
            const mouseX = event.clientX;
            const mouseY = event.clientY;

            // Calcula la rotación en base al movimiento del ratón
            targetRotationX = (mouseX - mouseXOnMouseDown) * dragFactor;
            targetRotationY = (mouseY - mouseYOnMouseDown) * dragFactor;
        }
    }

    function onDocumentMouseUp(event) {
        document.removeEventListener('mousemove', onDocumentMouseMove, false);
        document.removeEventListener('mouseup', onDocumentMouseUp, false);
        isDragging = false;
    }

    renderer.domElement.addEventListener('mousedown', onDocumentMouseDown, false);


    let scale = 1; // Escala inicial
    const maxScale = 2.5; // Escala máxima
    const minScale = 0.25; // Escala mínima (puedes ajustar esto si quieres permitir más reducción)

    function onDocumentWheel(event) {
        event.preventDefault(); // Evita el desplazamiento de la página

        // Cambiar la escala en función de la dirección de la rueda del ratón
        if (event.deltaY < 0) {
            scale += 0.1; // Ampliar
        } else {
            scale -= 0.1; // Disminuir
        }

        // Asegurarse de que la escala esté dentro de los límites
        scale = Math.min(maxScale, Math.max(minScale, scale));

        // Aplicar la escala a la tierra y capa de nubes
        earthMesh.scale.set(scale, scale, scale);
        cloudMesh.scale.set(scale,scale,scale);

        const distanceFromEarth = 2; // Distancia fija desde la Tierra en el eje Z
        pointLight.position.set(0.1 / scale, 0.1 / scale, distanceFromEarth);

    }

    // Añadir el evento de la rueda del ratón
    window.addEventListener('wheel', onDocumentWheel,  { passive: false });


    // Función de animación
    function animate() {
        requestAnimationFrame(animate);
        
        // Rotar la Tierra y la capa de nubes
        earthMesh.rotation.y += targetRotationX; // Rota la Tierra
        cloudMesh.rotation.y += targetRotationX; // Rota las nubes un poco más rápido para realismo
        earthMesh.rotation.x += targetRotationY; // Rota la Tierra
        cloudMesh.rotation.x += targetRotationY; // Rota las nubes un poco más rápido para realismo

        // Amortiguación de la velocidad de rotación
        rotationSpeedX *= dampingFactor;
        rotationSpeedY *= dampingFactor;

        // Aplicar la velocidad de rotación al modelo
        earthMesh.rotation.x += rotationSpeedY;
        earthMesh.rotation.y += rotationSpeedX;
        cloudMesh.rotation.x += rotationSpeedY; // Rota las nubes en el eje X también
        cloudMesh.rotation.y += rotationSpeedX;

        // Renderizar la escena
        renderer.render(scene, camera);
    }

    // Iniciar animación
    animate();

}

// Execute the 'main' function when the window finishes loading.
window.onload = main;