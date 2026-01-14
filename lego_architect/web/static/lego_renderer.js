/**
 * Enhanced LEGO Renderer with Data Validation and Performance Optimization
 *
 * Features:
 * - Pre-validation of API data
 * - Lazy loading for large builds (1000+ parts)
 * - Geometry caching
 * - Image preloading with fallbacks
 * - Memory management
 */

class LegoRenderer {
    constructor(scene, geometryLibrary) {
        this.scene = scene;
        this.geomLib = geometryLibrary;
        this.brickMeshes = new Map();
        this.renderQueue = [];
        this.isRendering = false;
        this.renderBatchSize = 50;  // Render 50 parts at a time
        this.validationErrors = [];
    }

    /**
     * Validate part data before rendering
     */
    validatePartData(part) {
        const errors = [];

        // Check required fields
        if (!part.id) errors.push(`Part missing ID`);
        if (!part.part_id) errors.push(`Part ${part.id} missing part_id`);
        if (typeof part.x !== 'number') errors.push(`Part ${part.id} has invalid x coordinate`);
        if (typeof part.y !== 'number') errors.push(`Part ${part.id} has invalid y coordinate`);
        if (typeof part.z !== 'number') errors.push(`Part ${part.id} has invalid z coordinate`);
        if (!part.color) errors.push(`Part ${part.id} missing color`);

        // Check dimensions
        if (!part.width || part.width <= 0) errors.push(`Part ${part.id} has invalid width`);
        if (!part.length || part.length <= 0) errors.push(`Part ${part.id} has invalid length`);
        if (!part.height || part.height <= 0) errors.push(`Part ${part.id} has invalid height`);

        // Check coordinate sanity (catch extreme values)
        if (Math.abs(part.x) > 10000) errors.push(`Part ${part.id} x coordinate out of range`);
        if (Math.abs(part.y) > 10000) errors.push(`Part ${part.id} y coordinate out of range`);
        if (Math.abs(part.z) > 10000) errors.push(`Part ${part.id} z coordinate out of range`);

        // Check rotation
        if (part.rotation && ![0, 90, 180, 270].includes(part.rotation)) {
            errors.push(`Part ${part.id} has invalid rotation ${part.rotation}`);
        }

        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }

    /**
     * Validate color exists and get hex value
     */
    getValidatedColor(colorCode, colors) {
        if (!colors[colorCode]) {
            console.warn(`Unknown color code ${colorCode}, using gray`);
            return '#888888';
        }
        return colors[colorCode].hex;
    }

    /**
     * Pre-validate image URL
     */
    async validateImageURL(url, timeout = 3000) {
        if (!url) return { valid: false, url: null };

        return new Promise((resolve) => {
            const img = new Image();
            const timer = setTimeout(() => {
                img.src = '';  // Cancel load
                resolve({ valid: false, url: null });
            }, timeout);

            img.onload = () => {
                clearTimeout(timer);
                resolve({ valid: true, url: url });
            };

            img.onerror = () => {
                clearTimeout(timer);
                resolve({ valid: false, url: null });
            };

            img.src = url;
        });
    }

    /**
     * Add single brick to scene with validation
     */
    addBrickToScene(part, colors) {
        // Validate part data
        const validation = this.validatePartData(part);
        if (!validation.isValid) {
            console.error(`Invalid part data:`, validation.errors);
            this.validationErrors.push(...validation.errors);
            return null;
        }

        try {
            // Get validated color
            const colorHex = this.getValidatedColor(part.color, colors);
            const material = this.geomLib.getMaterial(colorHex, part.is_transparent || false);

            // Calculate dimensions considering rotation
            let width = part.width;
            let length = part.length;
            if (part.rotation === 90 || part.rotation === 270) {
                [width, length] = [length, width];
            }

            // Determine part category from part_id or name
            let category = 'brick';
            if (part.part_name) {
                const nameLower = part.part_name.toLowerCase();
                if (nameLower.includes('plate')) category = 'plate';
                else if (nameLower.includes('tile')) category = 'tile';
                else if (nameLower.includes('slope')) category = 'slope';
                else if (nameLower.includes('technic')) category = 'technic';
            }

            // Create geometry using enhanced library
            const partInfo = {
                width: width,
                length: length,
                height: part.height,
                category: category,
                part_id: part.part_id
            };

            const brick = this.geomLib.createPartGeometry(partInfo);

            // Apply material to all meshes
            brick.traverse(child => {
                if (child instanceof THREE.Mesh) {
                    child.material = material.clone();
                    child.castShadow = true;
                    child.receiveShadow = true;
                }
            });

            // Position: convert stud coordinates to scene coordinates
            brick.position.set(
                part.x + width / 2,
                part.y / 3,  // Convert plates to brick units
                part.z + length / 2
            );

            // Apply rotation
            if (part.rotation) {
                brick.rotation.y = THREE.MathUtils.degToRad(part.rotation);
            }

            // Add to scene and track
            this.scene.add(brick);
            this.brickMeshes.set(part.id, brick);

            return brick;

        } catch (error) {
            console.error(`Error rendering part ${part.id}:`, error);
            this.validationErrors.push(`Failed to render part ${part.id}: ${error.message}`);
            return null;
        }
    }

    /**
     * Render parts with lazy loading for large builds
     */
    async renderBuild(build, colors) {
        this.validationErrors = [];

        // Validate build data
        if (!build || !build.parts || !Array.isArray(build.parts)) {
            console.error('Invalid build data structure');
            return { success: false, errors: ['Invalid build data'] };
        }

        // Clear existing scene
        this.clearScene();

        // For large builds (1000+ parts), use lazy loading
        if (build.parts.length > 1000) {
            return this.renderLazy(build.parts, colors);
        } else {
            // Render all parts immediately
            build.parts.forEach(part => this.addBrickToScene(part, colors));

            return {
                success: this.validationErrors.length === 0,
                errors: this.validationErrors,
                partsRendered: this.brickMeshes.size
            };
        }
    }

    /**
     * Lazy rendering for large builds
     */
    async renderLazy(parts, colors) {
        this.renderQueue = [...parts];
        this.isRendering = true;

        const startTime = performance.now();
        let rendered = 0;

        while (this.renderQueue.length > 0 && this.isRendering) {
            const batch = this.renderQueue.splice(0, this.renderBatchSize);

            batch.forEach(part => {
                if (this.addBrickToScene(part, colors)) {
                    rendered++;
                }
            });

            // Update progress
            const progress = ((parts.length - this.renderQueue.length) / parts.length) * 100;
            this.onProgress?.(progress);

            // Yield to browser for rendering
            await new Promise(resolve => setTimeout(resolve, 0));
        }

        const duration = performance.now() - startTime;

        return {
            success: this.validationErrors.length === 0,
            errors: this.validationErrors,
            partsRendered: rendered,
            duration: duration,
            skipped: parts.length - rendered
        };
    }

    /**
     * Clear all bricks from scene
     */
    clearScene() {
        this.brickMeshes.forEach((mesh, id) => {
            this.scene.remove(mesh);
            // Dispose geometry and materials to free memory
            mesh.traverse(child => {
                if (child instanceof THREE.Mesh) {
                    child.geometry?.dispose();
                    child.material?.dispose();
                }
            });
        });
        this.brickMeshes.clear();
        this.renderQueue = [];
        this.isRendering = false;
        this.validationErrors = [];
    }

    /**
     * Get rendering stats
     */
    getStats() {
        return {
            partsInScene: this.brickMeshes.size,
            queuedParts: this.renderQueue.length,
            validationErrors: this.validationErrors.length
        };
    }

    /**
     * Stop lazy rendering
     */
    stopRendering() {
        this.isRendering = false;
        this.renderQueue = [];
    }

    /**
     * Set progress callback for lazy rendering
     */
    setProgressCallback(callback) {
        this.onProgress = callback;
    }
}

// Export for use in main app
window.LegoRenderer = LegoRenderer;
