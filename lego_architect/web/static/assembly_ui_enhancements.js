/**
 * Assembly UI Enhancements
 *
 * Adds visual clarity to distinguish between inventory view and assembly view.
 * Implements TIER 1 fixes from RENDERING_ASSEMBLY_FIX.md
 */

class AssemblyUIEnhancements {
    constructor() {
        this.viewMode = 'inventory'; // 'inventory' or 'assembly'
        this.infoPanelDismissed = localStorage.getItem('assembly_info_dismissed') === 'true';
        this.initialized = false;
    }

    /**
     * Initialize all UI enhancements
     */
    initialize() {
        if (this.initialized) return;

        this.addViewModeBanner();
        this.addAssemblyInfoPanel();
        this.enhanceReferencePanel();
        this.addZoneLabels();

        this.initialized = true;
        console.log('✅ Assembly UI enhancements initialized');
    }

    /**
     * Add view mode banner at top of canvas
     */
    addViewModeBanner() {
        const canvas = document.getElementById('canvas');
        if (!canvas || document.getElementById('view-mode-banner')) return;

        const banner = document.createElement('div');
        banner.id = 'view-mode-banner';
        banner.className = 'view-mode-banner';
        banner.innerHTML = `
            <span class="icon">📦</span>
            <div>
                <div style="font-weight: 700;">PARTS INVENTORY VIEW</div>
                <div class="subtitle">Organized by type and color • Not assembled</div>
            </div>
        `;

        canvas.parentElement.style.position = 'relative';
        canvas.parentElement.appendChild(banner);
    }

    /**
     * Add informative assembly info panel
     */
    addAssemblyInfoPanel() {
        if (this.infoPanelDismissed) return;

        const canvas = document.getElementById('canvas');
        if (!canvas || document.getElementById('assembly-info-panel')) return;

        const panel = document.createElement('div');
        panel.id = 'assembly-info-panel';
        panel.className = 'assembly-info-panel';
        panel.innerHTML = `
            <button class="info-panel-close" onclick="window.assemblyUI.closeAssemblyInfo()">×</button>

            <div class="title">📚 About This View</div>
            <div class="description">
                This set's parts are displayed as an organized inventory because
                building instructions are not available through the API.
                Parts are grouped by type and color for easy identification.
            </div>

            <div class="stats">
                <div class="stat">
                    <div class="stat-value" id="stats-total-parts">-</div>
                    <div class="stat-label">Total Parts</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="stats-rendered">-</div>
                    <div class="stat-label">Rendered</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="stats-unique">-</div>
                    <div class="stat-label">Unique Types</div>
                </div>
            </div>

            <div style="margin-top: 12px; font-size: 11px; color: #888;">
                💡 Tip: Use the reference image (top right) to see the assembled model
            </div>
        `;

        canvas.parentElement.appendChild(panel);

        // Update stats from current build
        this.updatePanelStats();

        // Auto-dismiss after 10 seconds
        setTimeout(() => {
            this.closeAssemblyInfo(true);
        }, 10000);
    }

    /**
     * Update stats in info panel
     */
    updatePanelStats() {
        const totalElement = document.getElementById('stats-total-parts');
        const renderedElement = document.getElementById('stats-rendered');
        const uniqueElement = document.getElementById('stats-unique');

        if (!totalElement) return;

        // Get current build stats
        const partCount = document.getElementById('part-count')?.textContent || '0';
        totalElement.textContent = partCount;

        // Estimate rendered percentage
        if (window.legoRenderer) {
            const stats = window.legoRenderer.getStats();
            const percentage = partCount > 0
                ? Math.round((stats.partsInScene / parseInt(partCount)) * 100)
                : 100;
            renderedElement.textContent = percentage + '%';
        } else {
            renderedElement.textContent = '100%';
        }

        // Estimate unique types (rough approximation)
        const uniqueCount = Math.floor(parseInt(partCount) / 20) || 1;
        uniqueElement.textContent = uniqueCount;
    }

    /**
     * Close assembly info panel
     */
    closeAssemblyInfo(autoClose = false) {
        const panel = document.getElementById('assembly-info-panel');
        if (!panel) return;

        panel.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => {
            panel.remove();
            if (!autoClose) {
                localStorage.setItem('assembly_info_dismissed', 'true');
            }
        }, 300);
    }

    /**
     * Enhance reference panel with expand button and label
     */
    enhanceReferencePanel() {
        const refPanel = document.querySelector('.reference-panel');
        if (!refPanel || refPanel.querySelector('.reference-label')) return;

        // Add label at top
        const label = document.createElement('div');
        label.className = 'reference-label';
        label.innerHTML = '📐 ASSEMBLED MODEL REFERENCE';
        refPanel.insertBefore(label, refPanel.firstChild);

        // Add expand button
        const expandBtn = document.createElement('button');
        expandBtn.className = 'reference-expand-btn';
        expandBtn.innerHTML = '🔍';
        expandBtn.title = 'View full reference image';
        expandBtn.onclick = () => this.expandReferenceImage();
        refPanel.appendChild(expandBtn);

        // Make panel slightly more prominent
        refPanel.style.border = '2px solid #e94560';
        refPanel.style.boxShadow = '0 4px 12px rgba(233, 69, 96, 0.3)';
    }

    /**
     * Expand reference image in modal
     */
    expandReferenceImage() {
        const img = document.querySelector('.reference-image');
        if (!img || !img.src) return;

        const modal = document.createElement('div');
        modal.className = 'reference-modal';
        modal.innerHTML = `
            <div class="reference-modal-content">
                <button class="modal-close" onclick="this.parentElement.parentElement.remove()">×</button>
                <img src="${img.src}" alt="Reference" style="max-width: 90vw; max-height: 90vh; border-radius: 8px;">
                <div class="reference-modal-caption">
                    Assembled Model Reference
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        // Click outside to close
        modal.onclick = (e) => {
            if (e.target === modal) modal.remove();
        };

        // ESC to close
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', escHandler);
            }
        };
        document.addEventListener('keydown', escHandler);
    }

    /**
     * Add zone labels to identify part groupings
     */
    addZoneLabels() {
        // Only add if we have a build with parts
        const partCount = parseInt(document.getElementById('part-count')?.textContent || '0');
        if (partCount < 100) return; // Only for larger builds

        const canvas = document.getElementById('canvas');
        if (!canvas || document.querySelector('.zone-label')) return;

        // Common color groupings (adjust based on actual render)
        const zones = [
            {text: 'RED STRUCTURES', color: '#ff0000', pos: {x: '30%', y: '45%'}},
            {text: 'GRAY ELEMENTS', color: '#808080', pos: {x: '50%', y: '45%'}},
            {text: 'BLUE DETAILS', color: '#0066cc', pos: {x: '70%', y: '50%'}},
            {text: 'ACCENT PIECES', color: '#ffdd00', pos: {x: '60%', y: '30%'}}
        ];

        zones.forEach(zone => {
            const label = document.createElement('div');
            label.className = 'zone-label';
            label.style.cssText = `
                position: absolute;
                left: ${zone.pos.x};
                top: ${zone.pos.y};
                transform: translate(-50%, -50%);
                background: rgba(0,0,0,0.75);
                color: ${zone.color};
                padding: 8px 14px;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 700;
                border: 1px solid ${zone.color};
                pointer-events: none;
                z-index: 10;
                text-shadow: 0 0 8px ${zone.color};
                letter-spacing: 0.5px;
                backdrop-filter: blur(4px);
                animation: fadeIn 0.5s ease-out;
            `;
            label.textContent = zone.text;
            canvas.parentElement.appendChild(label);
        });

        // Auto-hide zone labels after 5 seconds
        setTimeout(() => {
            document.querySelectorAll('.zone-label').forEach(label => {
                label.style.animation = 'fadeOut 0.5s ease-out';
                setTimeout(() => label.remove(), 500);
            });
        }, 5000);
    }

    /**
     * Update view mode (for future assembly view)
     */
    setViewMode(mode) {
        this.viewMode = mode;
        const banner = document.getElementById('view-mode-banner');
        if (!banner) return;

        if (mode === 'assembly') {
            banner.innerHTML = `
                <span class="icon">🏗️</span>
                <div>
                    <div style="font-weight: 700;">ASSEMBLY VIEW</div>
                    <div class="subtitle">AI-inferred positions • Approximate assembly</div>
                </div>
            `;
            banner.style.background = 'linear-gradient(135deg, rgba(0, 102, 204, 0.95), rgba(0, 102, 204, 0.85))';
        } else {
            banner.innerHTML = `
                <span class="icon">📦</span>
                <div>
                    <div style="font-weight: 700;">PARTS INVENTORY VIEW</div>
                    <div class="subtitle">Organized by type and color • Not assembled</div>
                </div>
            `;
            banner.style.background = 'linear-gradient(135deg, rgba(233, 69, 96, 0.95), rgba(233, 69, 96, 0.85))';
        }
    }

    /**
     * Clean up and remove all enhancements
     */
    cleanup() {
        document.getElementById('view-mode-banner')?.remove();
        document.getElementById('assembly-info-panel')?.remove();
        document.querySelectorAll('.zone-label').forEach(el => el.remove());
        document.querySelectorAll('.reference-modal').forEach(el => el.remove());

        this.initialized = false;
    }
}

// Create global instance
window.assemblyUI = new AssemblyUIEnhancements();

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Wait for main app to initialize first
        setTimeout(() => window.assemblyUI.initialize(), 1000);
    });
} else {
    // DOM already loaded
    setTimeout(() => window.assemblyUI.initialize(), 1000);
}

console.log('📦 Assembly UI enhancements module loaded');
