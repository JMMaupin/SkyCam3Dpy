// Global variables for scene objects
let scene, camera, renderer, controls;
let masts = [];
let ropes = [];
let spar, ground;
let axesHelper;
let mastLabels = [];

// Static parameters received once from Python
const params = {
    masts: [
        { height: 5, x: -5, z: -3 },
        { height: 5, x: 5, z: -3 },
        { height: 5, x: 5, z: 3 },
        { height: 5, x: -5, z: 3 }
    ],
    spar: {
        width: 0.5,
        length: 0.3
    },
    showAxes: false
};

// Dynamic parameters updated en temps réel
let dynParams = {
    ropes: [
        { length: 7 },
        { length: 7 },
        { length: 7 },
        { length: 7 }
    ],
    sparPosition: { x: 0, y: 1, z: 0 }
};

// Initialize the Three.js scene, camera, renderer and controls
function init() {
    scene = new THREE.Scene();
    scene.fog = new THREE.FogExp2(0x999999, 0.05);

    camera = new THREE.PerspectiveCamera(
        75,
        window.innerWidth / window.innerHeight,
        0.1,
        1000
    );

    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    document.body.appendChild(renderer.domElement);

    controls = new THREE.OrbitControls(camera, renderer.domElement);
    camera.position.set(1, 2, 8);
    controls.update();
    camera.lookAt(new THREE.Vector3(0, 1, 0));

    // Ambient light
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    // Directional light with shadows
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(3, 20, 10);
    directionalLight.castShadow = true;
    directionalLight.shadow.camera.left = -50;
    directionalLight.shadow.camera.right = 50;
    directionalLight.shadow.camera.top = 50;
    directionalLight.shadow.camera.bottom = -50;
    directionalLight.shadow.camera.near = 0.1;
    directionalLight.shadow.camera.far = 200;
    directionalLight.shadow.mapSize.width = 4096;
    directionalLight.shadow.mapSize.height = 4096;
    scene.add(directionalLight);

    // Axes helper
    axesHelper = new THREE.AxesHelper(1);
    axesHelper.position.y = 0.1;
    scene.add(axesHelper);

    // Gradient background using shader material
    const vertexShader = `
        varying vec3 vWorldPosition;
        void main() {
            vec4 worldPosition = modelMatrix * vec4(position, 1.0);
            vWorldPosition = worldPosition.xyz;
            gl_Position = projectionMatrix * viewMatrix * worldPosition;
        }
    `;
    const fragmentShader = `
        varying vec3 vWorldPosition;
        void main() {
            float h = normalize(vWorldPosition).y;
            float offset = -0.5;
            vec3 topColor = vec3(0.4, 0.7, 0.98);
            vec3 bottomColor = vec3(1.0, 0.65, 0.0);
            gl_FragColor = vec4(mix(bottomColor, topColor, max(h * 0.5 + 0.5 - offset, 0.0)), 1.0);
        }
    `;
    const gradientMaterial = new THREE.ShaderMaterial({
        vertexShader: vertexShader,
        fragmentShader: fragmentShader,
        side: THREE.BackSide
    });
    const gradientGeometry = new THREE.SphereGeometry(500, 32, 32);
    const gradientMesh = new THREE.Mesh(gradientGeometry, gradientMaterial);
    scene.add(gradientMesh);

    // Initialize scene objects and GUI
    initScene();
    setupGUI();
    animate();

    // Update size on window resize
    window.addEventListener('resize', onWindowResize, false);
}

// Window resize handler
function onWindowResize() {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
}

// Create a text label using FontLoader
function createTextLabel(text, position) {
    const loader = new THREE.FontLoader();
    loader.load('https://threejs.org/examples/fonts/helvetiker_regular.typeface.json', function(font) {
        const textGeometry = new THREE.TextGeometry(text, {
            font: font,
            size: 0.2,
            height: 0.05,
        });
        const textMaterial = new THREE.MeshPhongMaterial({ color: 0xffffff });
        const textMesh = new THREE.Mesh(textGeometry, textMaterial);
        textMesh.position.copy(position);
        scene.add(textMesh);
        mastLabels.push(textMesh);
    });
}

// Remove all text labels from the scene
function removeTextLabels() {
    mastLabels.forEach(label => scene.remove(label));
    mastLabels = [];
}

// Initialize or reset scene objects (masts, spar, ropes, ground)
function initScene() {
    // Remove previous objects if any
    masts.forEach(mast => scene.remove(mast));
    ropes.forEach(rope => scene.remove(rope));
    if (spar) scene.remove(spar);
    if (ground) scene.remove(ground);
    removeTextLabels();

    // Create mast objects from params
    masts = [];
    const mastGeometry = new THREE.CylinderGeometry(0.1, 0.1, 1, 8);
    const mastMaterial = new THREE.MeshPhongMaterial({ color: 0x808080 });
    params.masts.forEach((mastParam, i) => {
        const mast = new THREE.Mesh(mastGeometry, mastMaterial);
        mast.castShadow = true;
        mast.receiveShadow = true;
        mast.position.set(mastParam.x, mastParam.height / 2, mastParam.z);
        mast.scale.y = mastParam.height;
        masts.push(mast);
        scene.add(mast);
        // Create a label near each mast
        createTextLabel(`${i + 1}`, new THREE.Vector3(mastParam.x, mastParam.height + 0.1, mastParam.z));
    });

    // Create the spar object
    const rectangleGeometry = new THREE.PlaneGeometry(params.spar.width, params.spar.length);
    const rectangleMaterial = new THREE.MeshPhongMaterial({ color: 0x00ff00, side: THREE.DoubleSide });
    spar = new THREE.Mesh(rectangleGeometry, rectangleMaterial);
    spar.rotation.x = Math.PI / 2;
    spar.castShadow = true;
    scene.add(spar);

    // Create rope objects connecting masts to the spar
    ropes = [];
    const ropeMaterial = new THREE.LineBasicMaterial({ color: 0xff0000 });
    for (let i = 0; i < params.masts.length; i++) {
        const ropeGeometry = new THREE.BufferGeometry();
        const line = new THREE.Line(ropeGeometry, ropeMaterial);
        line.castShadow = true;
        ropes.push(line);
        scene.add(line);
    }

    // Create the ground based on mast positions
    updateGround();
    // Initial update of all geometry positions
    updateGeometry();
}

// Update the ground plane dimensions and position
function updateGround() {
    if (ground) scene.remove(ground);
    const xs = params.masts.map(m => m.x);
    const zs = params.masts.map(m => m.z);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minZ = Math.min(...zs);
    const maxZ = Math.max(...zs);
    const width = (maxX - minX) * 1.2;
    const depth = (maxZ - minZ) * 1.2;
    const centerX = (minX + maxX) / 2;
    const centerZ = (minZ + maxZ) / 2;
    const groundGeometry = new THREE.PlaneGeometry(width, depth);
    const groundMaterial = new THREE.MeshPhongMaterial({ color: 0x707070, side: THREE.DoubleSide });
    ground = new THREE.Mesh(groundGeometry, groundMaterial);
    ground.rotation.x = -Math.PI / 2;
    ground.position.set(centerX, 0, centerZ);
    ground.receiveShadow = true;
    scene.add(ground);
}

// A simple method to calculate a central position; here, on peut l'adapter selon vos besoins
function calculateCentralPosition() {
    let sumX = 0, sumY = 0, sumZ = 0;
    const count = params.masts.length;
    masts.forEach((mast, i) => {
        sumX += mast.position.x;
        sumY += mast.position.y + params.masts[i].height / 2;
        sumZ += mast.position.z;
    });
    return new THREE.Vector3(sumX / count, sumY / count, sumZ / count);
}

// Update the spar and rope geometries based on updated parameters
function updateGeometry() {
    // Update each mast's position and scale according to params
    params.masts.forEach((mastParam, i) => {
        masts[i].position.set(mastParam.x, mastParam.height / 2, mastParam.z);
        masts[i].scale.y = mastParam.height;
    });
    removeTextLabels();
    // Recreate the mast labels
    params.masts.forEach((mastParam, i) => {
        createTextLabel(`${i + 1}`, new THREE.Vector3(mastParam.x, mastParam.height + 0.1, mastParam.z));
    });

    // Update spar position: use dynamic sparPosition if provided; otherwise, calculate center
    updateRopesAndSpar();

    // Update ground and axes visibility
    updateGround();
    updateAxesHelper();
}

// Toggle axes helper visibility
function updateAxesHelper() {
    axesHelper.visible = params.showAxes;
}

// Setup dat.GUI for real-time parameter adjustments
function setupGUI() {
    const gui = new dat.GUI();
    
    const mastFolder = gui.addFolder('Mast Height');
    params.masts.forEach((mast, i) => {
        mastFolder.add(mast, 'height', 1, 10).name(`Mast ${i+1}`).onChange(updateGeometry);
    });
    mastFolder.close(); // Close the folder by default
    
    const positionFolder = gui.addFolder('Mast Position');
    params.masts.forEach((mast, i) => {
        positionFolder.add(mast, 'x', -10, 10).name(`Mast ${i+1} X`).onChange(updateGeometry);
        positionFolder.add(mast, 'z', -10, 10).name(`Mast ${i+1} Z`).onChange(updateGeometry);
    });
    positionFolder.close(); // Close the folder by default
    
    const ropeFolder = gui.addFolder('Rope Length');
    dynParams.ropes.forEach((rope, i) => {
        ropeFolder.add(rope, 'length', 1, 10).name(`Rope ${i+1}`).onChange(updateGeometry);
    });
    ropeFolder.close(); // Close the folder by default
    
    const sparFolder = gui.addFolder('Spar');
    sparFolder.add(params.spar, 'width', 0.1, 2).name('Width').onChange(() => {
        spar.geometry.dispose();
        spar.geometry = new THREE.PlaneGeometry(params.spar.width, params.spar.length);
        updateGeometry();
    });
    sparFolder.add(params.spar, 'length', 0.1, 2).name('Length').onChange(() => {
        spar.geometry.dispose();
        spar.geometry = new THREE.PlaneGeometry(params.spar.width, params.spar.length);
        updateGeometry();
    });
    sparFolder.close(); // Close the folder by default
    
    gui.add(params, 'showAxes').name('Show Axes').onChange(updateAxesHelper);

    gui.close(); // Close the folder by default
}
// Animation loop
function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}

// Expose functions via Eel to receive parameters from Python
eel.expose(upload_params);
function upload_params(receivedParams) {
    Object.assign(params, receivedParams);
    updateGeometry();
}

eel.expose(update_dynParams);
function update_dynParams(receivedDynParams) {
    Object.assign(dynParams, receivedDynParams);
    updateRopesAndSpar();
}

// Function to update only ropes and spar based on dynamic parameters
function updateRopesAndSpar() {
    // Update spar position: use dynamic sparPosition if provided; otherwise, calculate center
    if (dynParams.sparPosition) {
        spar.position.set(dynParams.sparPosition.x, dynParams.sparPosition.y, dynParams.sparPosition.z);
    } else {
        let center = calculateCentralPosition();
        spar.position.copy(center);
    }

    // Compute corners of the spar (assuming axis-aligned spar)
    const halfWidth = params.spar.width / 2;
    const halfLength = params.spar.length / 2;
    const corners = [
        new THREE.Vector3(spar.position.x - halfWidth, spar.position.y, spar.position.z - halfLength),
        new THREE.Vector3(spar.position.x + halfWidth, spar.position.y, spar.position.z - halfLength),
        new THREE.Vector3(spar.position.x + halfWidth, spar.position.y, spar.position.z + halfLength),
        new THREE.Vector3(spar.position.x - halfWidth, spar.position.y, spar.position.z + halfLength)
    ];

    // Update each rope to connect the top of a mast to the corresponding spar corner
    ropes.forEach((rope, i) => {
        const mastTop = new THREE.Vector3(
            masts[i].position.x,
            masts[i].position.y + params.masts[i].height / 2,
            masts[i].position.z
        );
        const points = [mastTop, corners[i]];
        rope.geometry.setFromPoints(points);
        rope.geometry.attributes.position.needsUpdate = true;
    });
}

// Start everything
init();
