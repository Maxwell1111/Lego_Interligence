/**
 * LEGO Geometry Library - Accurate part rendering for Three.js
 *
 * Generates detailed LEGO part geometries with proper studs, tubes, and shapes.
 * Includes caching for performance optimization.
 */

class LegoGeometryLibrary {
    constructor() {
        this.geometryCache = new Map();
        this.materialCache = new Map();

        // LEGO dimensions (in scene units, 1 unit = 1 stud)
        this.STUD_RADIUS = 0.25;
        this.STUD_HEIGHT = 0.18;
        this.TUBE_RADIUS = 0.32;
        this.TUBE_HEIGHT = 0.9;
        this.BRICK_HEIGHT = 0.96;  // Standard brick (3 plates)
        this.PLATE_HEIGHT = 0.32;  // Single plate
    }

    /**
     * Get or create cached material
     */
    getMaterial(color, isTransparent = false) {
        const key = `${color}_${isTransparent}`;

        if (this.materialCache.has(key)) {
            return this.materialCache.get(key).clone();
        }

        const material = new THREE.MeshPhongMaterial({
            color: color,
            shininess: 80,
            specular: 0x222222,
            transparent: isTransparent,
            opacity: isTransparent ? 0.7 : 1.0,
            side: THREE.DoubleSide
        });

        this.materialCache.set(key, material);
        return material.clone();
    }

    /**
     * Create standard LEGO stud geometry
     */
    createStud() {
        const key = 'stud';
        if (this.geometryCache.has(key)) {
            return this.geometryCache.get(key).clone();
        }

        const group = new THREE.Group();

        // Main cylinder
        const cylinderGeom = new THREE.CylinderGeometry(
            this.STUD_RADIUS,
            this.STUD_RADIUS,
            this.STUD_HEIGHT,
            16
        );
        const cylinder = new THREE.Mesh(cylinderGeom);
        cylinder.position.y = this.STUD_HEIGHT / 2;
        group.add(cylinder);

        // Top chamfer (slight bevel)
        const chamferGeom = new THREE.CylinderGeometry(
            this.STUD_RADIUS * 0.95,
            this.STUD_RADIUS,
            this.STUD_HEIGHT * 0.1,
            16
        );
        const chamfer = new THREE.Mesh(chamferGeom);
        chamfer.position.y = this.STUD_HEIGHT * 0.95;
        group.add(chamfer);

        this.geometryCache.set(key, group);
        return group.clone();
    }

    /**
     * Create bottom tubes (anti-studs)
     */
    createTubes(width, length) {
        const tubes = new THREE.Group();

        // Add tubes at each interior position
        for (let x = 0; x < width; x++) {
            for (let z = 0; z < length; z++) {
                const tubeGeom = new THREE.CylinderGeometry(
                    this.TUBE_RADIUS,
                    this.TUBE_RADIUS,
                    this.TUBE_HEIGHT,
                    16
                );
                const tube = new THREE.Mesh(tubeGeom);
                tube.position.set(
                    x - (width - 1) / 2,
                    -this.TUBE_HEIGHT / 2,
                    z - (length - 1) / 2
                );
                tubes.add(tube);
            }
        }

        return tubes;
    }

    /**
     * Create standard brick geometry
     */
    createBrick(width, length, height, category = 'brick') {
        const key = `${category}_${width}x${length}x${height}`;

        const group = new THREE.Group();
        const actualHeight = height / 3;  // Convert plates to brick units

        // Main body with rounded edges
        const bodyGeom = new THREE.BoxGeometry(width, actualHeight * 0.96, length);
        const bodyMesh = new THREE.Mesh(bodyGeom);
        bodyMesh.position.y = actualHeight * 0.48;

        // Apply edge beveling
        const edges = new THREE.EdgesGeometry(bodyGeom);
        const line = new THREE.LineSegments(
            edges,
            new THREE.LineBasicMaterial({ color: 0x000000, opacity: 0.1, transparent: true })
        );
        bodyMesh.add(line);

        group.add(bodyMesh);

        // Add studs on top (not for tiles)
        if (category !== 'tile' && height >= 1) {
            for (let x = 0; x < width; x++) {
                for (let z = 0; z < length; z++) {
                    const stud = this.createStud();
                    stud.position.set(
                        x - (width - 1) / 2,
                        actualHeight * 0.96,
                        z - (length - 1) / 2
                    );
                    group.add(stud);
                }
            }
        }

        // Add bottom tubes for bricks (not plates)
        if (height >= 3 && (width > 1 || length > 1)) {
            const tubes = this.createTubes(width, length);
            group.add(tubes);
        }

        return group;
    }

    /**
     * Create slope geometry (angled bricks)
     */
    createSlope(width, length, height, angle = 45) {
        const group = new THREE.Group();
        const actualHeight = height / 3;

        // Create custom slope geometry
        const shape = new THREE.Shape();
        shape.moveTo(-width/2, 0);
        shape.lineTo(width/2, 0);
        shape.lineTo(width/2, actualHeight);
        shape.lineTo(-width/2, 0);

        const extrudeSettings = {
            steps: 1,
            depth: length,
            bevelEnabled: false
        };

        const slopeGeom = new THREE.ExtrudeGeometry(shape, extrudeSettings);
        const slopeMesh = new THREE.Mesh(slopeGeom);
        slopeMesh.rotation.x = Math.PI / 2;
        slopeMesh.position.z = -length / 2;
        group.add(slopeMesh);

        // Add studs on top of slope
        for (let x = 0; x < width; x++) {
            for (let z = 0; z < length; z++) {
                const stud = this.createStud();
                const zPos = z - (length - 1) / 2;
                const yPos = actualHeight * (1 - z / length);  // Slope down
                stud.position.set(
                    x - (width - 1) / 2,
                    yPos,
                    zPos
                );
                group.add(stud);
            }
        }

        return group;
    }

    /**
     * Create round brick/plate
     */
    createRoundBrick(diameter, height) {
        const group = new THREE.Group();
        const actualHeight = height / 3;

        // Main cylinder
        const radius = diameter / 2;
        const cylinderGeom = new THREE.CylinderGeometry(
            radius,
            radius,
            actualHeight * 0.96,
            32
        );
        const cylinder = new THREE.Mesh(cylinderGeom);
        cylinder.position.y = actualHeight * 0.48;
        group.add(cylinder);

        // Center stud
        const stud = this.createStud();
        stud.position.y = actualHeight * 0.96;
        group.add(stud);

        return group;
    }

    /**
     * Create Technic brick with holes
     */
    createTechnicBrick(width, length, height) {
        const group = this.createBrick(width, length, height, 'technic');
        const actualHeight = height / 3;

        // Add holes through the brick
        for (let x = 0; x < width; x++) {
            const holeGeom = new THREE.CylinderGeometry(0.25, 0.25, length + 0.1, 16);
            const holeMesh = new THREE.Mesh(holeGeom);
            holeMesh.rotation.x = Math.PI / 2;
            holeMesh.position.set(
                x - (width - 1) / 2,
                actualHeight * 0.48,
                0
            );

            // Use CSG subtraction in production (requires library)
            // For now, visualize with dark rings
            const ringGeom = new THREE.TorusGeometry(0.25, 0.05, 8, 16);
            const ring = new THREE.Mesh(
                ringGeom,
                new THREE.MeshBasicMaterial({ color: 0x000000, opacity: 0.5, transparent: true })
            );
            ring.position.copy(holeMesh.position);
            ring.rotation.copy(holeMesh.rotation);
            group.add(ring);
        }

        return group;
    }

    /**
     * Main factory method - creates appropriate geometry based on part info
     */
    createPartGeometry(partInfo) {
        const { width, length, height, category = 'brick', part_id } = partInfo;

        // Determine part type and create appropriate geometry
        if (category === 'slope' || part_id.startsWith('303')) {
            return this.createSlope(width, length, height);
        } else if (category === 'technic' || part_id.startsWith('370')) {
            return this.createTechnicBrick(width, length, height);
        } else if (part_id.startsWith('6143') || part_id.startsWith('3062')) {
            return this.createRoundBrick(width, height);
        } else if (category === 'tile') {
            return this.createBrick(width, length, height, 'tile');
        } else {
            return this.createBrick(width, length, height, category);
        }
    }

    /**
     * Clear cache to free memory
     */
    clearCache() {
        this.geometryCache.clear();
        this.materialCache.forEach(mat => mat.dispose());
        this.materialCache.clear();
    }
}

// Export for use in main app
window.LegoGeometryLibrary = LegoGeometryLibrary;
