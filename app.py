<!DOCTYPE html>
<html lang="en" class="scroll-smooth">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Velsci Fit — 3D Garment Preview & Pattern Engine</title>

  <!-- Tailwind CSS, FontAwesome & Three.js for 3D Rendering -->
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>

  <style>
    body { font-family: 'Inter', sans-serif; background-color: #051410; color: #f8fafc; }
    .glass-card { background: rgba(10, 35, 27, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(31, 83, 66, 0.5); }
  </style>
</head>
<body class="min-h-screen flex flex-col justify-between p-4 sm:p-8">

  <!-- Security Access Modal -->
  <div id="authModal" class="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
    <div class="glass-card p-8 rounded-2xl max-w-md w-full text-center space-y-4 border border-emerald-500/30">
      <div class="w-12 h-12 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center mx-auto text-amber-400 text-xl">
        <i class="fa-solid fa-cube"></i>
      </div>
      <h3 class="text-xl font-bold text-white">Velsci Fit 3D Engine</h3>
      <p class="text-xs text-slate-300">Enter Access PIN to load 3D Preview Portal:</p>
      <input type="password" id="passcodeKey" placeholder="Enter Access PIN (2026)" class="w-full px-4 py-2.5 rounded-lg bg-[#051410] border border-emerald-800 text-white text-center font-mono text-base focus:outline-none focus:border-amber-400">
      <button onclick="verifyAccess()" class="w-full py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg text-sm transition-all">Launch 3D Engine</button>
      <p id="errMsg" class="text-xs text-rose-400 hidden">Invalid Security Passcode!</p>
    </div>
  </div>

  <!-- Main Protected Workspace -->
  <div id="protectedContent" class="max-w-6xl mx-auto w-full hidden space-y-6">
    
    <div class="flex justify-between items-center border-b border-emerald-800/60 pb-4">
      <div>
        <h1 class="text-2xl font-bold text-white flex items-center gap-2">
          <i class="fa-solid fa-cube text-amber-400"></i> Velsci Fit 3D Preview & Pattern Generator
        </h1>
        <p class="text-xs text-slate-400">360° Interactive 3D Mesh Inspection prior to Pattern Generation</p>
      </div>
      <a href="index.html" class="px-3 py-1.5 bg-emerald-900/60 hover:bg-emerald-800 border border-emerald-700/50 rounded-lg text-xs text-slate-200">
        ➔ Back to Main Site
      </a>
    </div>

    <!-- Controls Panel -->
    <div class="glass-card p-6 rounded-2xl space-y-4">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div>
          <label class="block text-xs font-semibold text-amber-400 uppercase mb-1">1. Garment Image:</label>
          <input type="file" id="imageInput" accept="image/*" class="w-full text-xs text-slate-300 file:mr-2 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:bg-emerald-800 file:text-white cursor-pointer">
        </div>

        <div>
          <label class="block text-xs font-semibold text-amber-400 uppercase mb-1">2. Reference Object:</label>
          <select id="refTypeSelect" class="w-full px-3 py-2 rounded-lg bg-[#051410] border border-emerald-800 text-xs text-white focus:outline-none">
            <option value="coin" data-size="23">₹5 / 1€ Coin (23 mm)</option>
            <option value="card" data-size="85.6">Credit / ID Card (85.6 mm)</option>
            <option value="note" data-size="123">Currency Note (123 mm)</option>
            <option value="ruler" data-size="150">Ruler / Scale (150 mm)</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-semibold text-amber-400 uppercase mb-1">3. A4 Puzzle Layout:</label>
          <select id="puzzleGridSelect" class="w-full px-3 py-2 rounded-lg bg-[#051410] border border-emerald-800 text-xs text-white focus:outline-none">
            <option value="3x3">3 x 3 (9 Pieces)</option>
            <option value="4x4" selected>4 x 4 (16 Pieces)</option>
            <option value="5x5">5 x 5 (25 Pieces)</option>
          </select>
        </div>

        <div>
          <label class="block text-xs font-semibold text-amber-400 uppercase mb-1">4. Seam Allowance (%):</label>
          <input type="number" id="cuttingMargin" value="10" class="w-full px-3 py-2 rounded-lg bg-[#051410] border border-emerald-800 text-xs text-white focus:outline-none">
        </div>

      </div>

      <div class="flex flex-wrap gap-3 pt-2">
        <button id="preview3dBtn" onclick="render3DPreview()" class="px-5 py-2.5 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold rounded-lg text-xs transition-all flex items-center gap-2">
          <i class="fa-solid fa-eye"></i>
          <span>1. Generate Interactive 3D Preview</span>
        </button>

        <button id="processBtn" onclick="processWithRenderBackend()" class="px-5 py-2.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded-lg text-xs transition-all flex items-center gap-2">
          <i class="fa-solid fa-puzzle-piece"></i>
          <span>2. Generate Printable 2D Pattern</span>
        </button>

        <button id="downloadBtn" onclick="downloadPattern()" class="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-lg text-xs transition-all hidden flex items-center gap-2">
          <i class="fa-solid fa-download"></i>
          <span>Download A4 Pattern</span>
        </button>
      </div>
    </div>

    <!-- 3D Display Canvas Viewport -->
    <div id="view3DCard" class="glass-card p-4 rounded-2xl flex flex-col items-center hidden">
      <div class="flex justify-between w-full mb-2 px-2 items-center">
        <span class="text-xs font-bold text-sky-400 uppercase tracking-wider flex items-center gap-2">
          <i class="fa-solid fa-arrows-spin animate-spin"></i> Interactive 3D Garment Canvas (Drag mouse to rotate 360°)
        </span>
        <span class="text-[10px] text-slate-400">Powered by Three.js WebGL</span>
      </div>
      <div id="canvas3DContainer" class="w-full h-80 rounded-xl bg-black/60 border border-sky-500/30 overflow-hidden"></div>
    </div>

    <!-- Output & Status -->
    <div id="statusBox" class="p-3 bg-amber-500/20 border border-amber-500/40 text-amber-300 rounded-lg text-xs font-mono text-center hidden"></div>

    <div id="patternOutput" class="glass-card p-5 rounded-xl border border-emerald-500/40 hidden">
      <h4 class="text-sm font-bold text-amber-400 mb-2">Pattern Measurement Summary:</h4>
      <div id="outputDetails" class="text-xs text-slate-200 leading-relaxed font-mono space-y-1"></div>
    </div>

    <!-- Processed 2D Printable Pattern Result -->
    <div class="glass-card p-4 rounded-2xl flex justify-center items-center overflow-auto">
      <img id="processedImgDisplay" class="max-w-full rounded-lg border border-dashed border-emerald-500/50 hidden" alt="Garment Pattern">
    </div>

  </div>

  <script>
    const ACCESS_PIN = "2026";
    const RENDER_BACKEND_URL = "https://velsci-fit-backend.onrender.com/process-pattern";

    function verifyAccess() {
      const inputKey = document.getElementById("passcodeKey").value;
      if (inputKey === ACCESS_PIN) {
        document.getElementById("authModal").classList.add("hidden");
        document.getElementById("protectedContent").classList.remove("hidden");
      } else {
        document.getElementById("errMsg").classList.remove("hidden");
      }
    }

    let base64Image = null;
    let resultBase64 = null;
    let scene, camera, renderer, controls, garmentMesh;

    document.getElementById('imageInput').addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
          base64Image = event.target.result;
        }
        reader.readAsDataURL(file);
      }
    });

    // Three.js 3D Interactive Preview Generator
    function render3DPreview() {
      if (!base64Image) {
        alert("Please upload a garment image first!");
        return;
      }

      document.getElementById('view3DCard').classList.remove('hidden');
      const container = document.getElementById('canvas3DContainer');
      container.innerHTML = '';

      // Initialize Three.js Scene
      scene = new THREE.Scene();
      camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 1000);
      camera.position.set(0, 0, 3.5);

      renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      renderer.setSize(container.clientWidth, container.clientHeight);
      container.appendChild(renderer.domElement);

      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;

      // Lights
      const ambientLight = new THREE.AmbientLight(0xffffff, 0.9);
      scene.add(ambientLight);
      const dirLight = new THREE.DirectionalLight(0xffd700, 0.6);
      dirLight.position.set(2, 3, 4);
      scene.add(dirLight);

      // Create 3D Curved Garment Mesh and map uploaded image as texture
      const texture = new THREE.TextureLoader().load(base64Image);
      const geometry = new THREE.CylinderGeometry(0.9, 1.0, 2.0, 32, 1, true, -Math.PI / 2.2, Math.PI / 1.1);
      const material = new THREE.MeshStandardMaterial({
        map: texture,
        side: THREE.DoubleSide,
        roughness: 0.5
      });

      garmentMesh = new THREE.Mesh(geometry, material);
      scene.add(garmentMesh);

      function animate() {
        requestAnimationFrame(animate);
        controls.update();
        renderer.render(scene, camera);
      }
      animate();
    }

    async function processWithRenderBackend() {
      if (!base64Image) {
        alert("Please upload a garment image first!");
        return;
      }

      const statusBox = document.getElementById('statusBox');
      const processBtn = document.getElementById('processBtn');
      const refSelect = document.getElementById('refTypeSelect');
      const selectedOption = refSelect.options[refSelect.selectedIndex];
      
      const gridVal = document.getElementById('puzzleGridSelect').value.split('x');

      statusBox.classList.remove('hidden');
      statusBox.innerText = "⏳ Processing image & generating printable puzzle pattern...";
      processBtn.disabled = true;

      const payload = {
        image: base64Image,
        ref_type: refSelect.value,
        known_width_mm: parseFloat(selectedOption.getAttribute('data-size')),
        margin: parseFloat(document.getElementById('cuttingMargin').value),
        grid_rows: parseInt(gridVal[0]),
        grid_cols: parseInt(gridVal[1])
      };

      try {
        const response = await fetch(RENDER_BACKEND_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (data.success) {
          statusBox.className = "p-3 bg-emerald-500/20 border border-emerald-500/40 text-emerald-300 rounded-lg text-xs font-mono text-center";
          statusBox.innerText = "✓ Pattern Generated Successfully!";

          resultBase64 = data.processed_image;
          const imgEl = document.getElementById('processedImgDisplay');
          imgEl.src = resultBase64;
          imgEl.classList.remove('hidden');

          document.getElementById('downloadBtn').classList.remove('hidden');
          document.getElementById('patternOutput').classList.remove('hidden');

          document.getElementById('outputDetails').innerHTML = `
            <div>• Measured Bounding Width: <b class="text-emerald-400">${data.measured_width_cm} cm</b></div>
            <div>• Measured Bounding Height: <b class="text-emerald-400">${data.measured_height_cm} cm</b></div>
            <div>• Generated Puzzle Tiles: <b class="text-amber-400">${data.total_puzzle_pieces} Pieces</b></div>
            <div class="pt-2 text-sm text-amber-400 font-bold">➔ Total Fabric Needed: ${data.required_meters} Meters</div>
          `;
        }
      } catch (err) {
        statusBox.className = "p-3 bg-rose-500/20 border border-rose-500/40 text-rose-300 rounded-lg text-xs font-mono text-center";
        statusBox.innerText = `❌ Error connecting to backend API.`;
      } finally {
        processBtn.disabled = false;
      }
    }

    function downloadPattern() {
      if (!resultBase64) return;
      const a = document.createElement('a');
      a.href = resultBase64;
      a.download = 'velsci-fit-3d-pattern.jpg';
      a.click();
    }
  </script>
</body>
</html>
