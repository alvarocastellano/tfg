function main() {
    // We now establish the core components: scene, renderer, and camera.
    const scene = new THREE.Scene();
    const renderer = new THREE.WebGLRenderer({ canvas: document.querySelector('#globe') });
    renderer.setSize(window.innerWidth, window.innerHeight);
    const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 1.7;


    const markers = [
        { lat: 50.8503, lng: 4.3517, cities: ['Bruselas'], country: 'Belgica', flag: 'belgica.png' },
        { lat: 42.6977, lng: 23.3219, cities: ['Sofia'], country: 'Bulgaria', flag: 'bulgaria.png' },
        { lat: 50.0755, lng: 14.4378, cities: ['Praga'], country: 'Chequia', flag: 'chequia.png' },
        { lat: 55.6761, lng: 12.5683, cities: ['Copenhague'], country: 'Dinamarca', flag: 'dinamarca.png' },
        { lat: 52.5200, lng: 13.4050, cities: ['Berlin','Munich'], country: 'Alemania', flag: 'alemania.png' },
        { lat: 59.4370, lng: 24.7536, cities: ['Tallin'], country: 'Estonia', flag: 'estonia.png' },
        { lat: 53.3498, lng: -6.2603, cities: ['Dublin','Cork'], country: 'Irlanda', flag: 'irlanda.png' },
        { lat: 37.9838, lng: 23.7275, cities: ['Atenas'], country: 'Grecia', flag: 'grecia.png' },
        { lat: 40.4168, lng: -3.7038, cities: ['Madrid','Sevilla','Barcelona'], country: 'España', flag: 'spain.png' },
        { lat: 48.8566, lng: 2.3522, cities: ['Paris','Lens','Marsella'], country: 'Francia', flag: 'francia.png' },
        { lat: 45.8150, lng: 15.9819, cities: ['Zagreb','Split'], country: 'Croacia', flag: 'croacia.png' },
        { lat: 41.9028, lng: 12.4964, cities: ['Roma','Salerno','Florencia','Bari'], country: 'Italia', flag: 'italia.png' },
        { lat: 49.6116, lng: 6.1319, cities: ['Luxemburgo'], country: 'Luxemburgo', flag: 'luxemburgo.png' },
        { lat: 47.4979, lng: 19.0402, cities: ['Budapest'], country: 'Hungria', flag: 'hungria.png' },
        { lat: 35.8989, lng: 14.5146, cities: ['La Valeta'], country: 'Malta', flag: 'malta.png' },
        { lat: 52.3676, lng: 4.9041, cities: ['Amsterdam','Roterdam'], country: 'Paises Bajos', flag: 'holanda.png' },
        { lat: 48.2082, lng: 16.3738, cities: ['Viena'], country: 'Austria', flag: 'austria.png' },
        { lat: 52.2297, lng: 21.0122, cities: ['Varsovia'], country: 'Polonia', flag: 'polonia.png' },
        { lat: 38.7223, lng: -9.1393, cities: ['Lisboa','Oporto'], country: 'Portugal', flag: 'portugal.png' },
    ];

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
    const pointLight = new THREE.PointLight(0xffffff, 1.5, 3.5,-1);
    pointLight.position.set(0.1, 0.1, 1);
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
    const dragFactor = 0.0001;

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


    
    //OJO: MARCADORES NO FUNCIONAN
    //PORQUE SON EN 2D Y NO CALCULO BIEN SUS POSICIONES RESPECTO A LA ESFERA 3D (TIERRA)????


    
    
    
    // Coloca los marcadores como hijos de earthMesh para que se sincronicen con la rotación de la Tierra
    markers.forEach(marker => {
        const { lat, lng } = marker;
        const position = latLngToVector3(lat, lng, 0.52); // Ajusta el radio según tu esfera
        const sprite = new THREE.Sprite(markerMaterial);
        sprite.position.copy(position);
        sprite.scale.set(0.03, 0.03, 1); // Ajusta el tamaño del marcador
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


    //OJO: QUIERO QUE AL SOLTAR EL RATON NO SIGA ROTANDO INFINITAMENTE, PERO NO FUNCIONA
    
    // Define functions that handle mouse events for interaction with the Globe.
    let rotationSpeedX = 0;
    let rotationSpeedY = 0;
    let isDragging = false; // Variable para comprobar si el ratón está siendo arrastrado
    const dampingFactor = 0.9; // Factor de amortiguación para que se suavice
    const stopThreshold = 0.0001; // Umbral para detener la rotación

    function onDocumentMouseDown(event) {
        event.preventDefault();
        document.addEventListener('mousemove', onDocumentMouseMove, false);
        document.addEventListener('mouseup', onDocumentMouseUp, false);
        mouseXOnMouseDown = event.clientX - windowHalfX;
        mouseYOnMouseDown = event.clientY - windowHalfY;
        isDragging = true; // Comenzamos a arrastrar
    }

    function onDocumentMouseMove(event) {
        mouseX = event.clientX - windowHalfX;
        rotationSpeedX = (mouseX - mouseXOnMouseDown) * dragFactor;
        mouseY = event.clientY - windowHalfY;
        rotationSpeedY = (mouseY - mouseYOnMouseDown) * dragFactor;

        targetRotationX = rotationSpeedX;
        targetRotationY = rotationSpeedY;
    }

    function onDocumentMouseUp(event) {
        document.removeEventListener('mousemove', onDocumentMouseMove, false);
        document.removeEventListener('mouseup', onDocumentMouseUp, false);
        isDragging = false; // Detenemos el arrastre al soltar el ratón
    
        // Guarda la velocidad actual al soltar el ratón
        rotationSpeedX = (mouseX - mouseXOnMouseDown) * dragFactor * 0.5; // Ajusta el factor si es necesario
        rotationSpeedY = (mouseY - mouseYOnMouseDown) * dragFactor * 0.5;
    }
    

    // Step 10
    // Add an Event listener to the document for the mousedown event.
    document.addEventListener('mousedown', onDocumentMouseDown, false); 
    

    const render = () => {
        // Si no estamos arrastrando, aplicamos la amortiguación
        if (!isDragging) {
            // Suavizar la velocidad de rotación
            rotationSpeedX *= dampingFactor; // Reduce la velocidad lentamente
            rotationSpeedY *= dampingFactor;
    
            // Detenemos la rotación si la velocidad es suficientemente baja
            if (Math.abs(rotationSpeedX) < stopThreshold) rotationSpeedX = 0;
            if (Math.abs(rotationSpeedY) < stopThreshold) rotationSpeedY = 0;
        }
    
        // Aplicar la rotación
        earthMesh.rotateOnWorldAxis(new THREE.Vector3(0, 1, 0), rotationSpeedX);
        earthMesh.rotateOnWorldAxis(new THREE.Vector3(1, 0, 0), rotationSpeedY);
        cloudMesh.rotateOnWorldAxis(new THREE.Vector3(0, 1, 0), rotationSpeedX);
        cloudMesh.rotateOnWorldAxis(new THREE.Vector3(1, 0, 0), rotationSpeedY);
    
        renderer.render(scene, camera);
    };

    const animate = () => {
        requestAnimationFrame(animate);
        render();
    }

    animate();
}

// Execute the 'main' function when the window finishes loading.
window.onload = main;