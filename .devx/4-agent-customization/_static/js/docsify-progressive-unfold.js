(function () {
    'use strict';

    function progressiveUnfoldPlugin(hook, vm) {
        let sections = [];
        let currentSection = 0;
        let navContainer = null;
        let prevBtn = null;
        let nextBtn = null;

        // Cookie helpers
        function getCookieKey() {
            return `docsify-unfold-${encodeURIComponent(vm.route.path)}`;
        }

        function saveProgress() {
            const key = getCookieKey();
            document.cookie = `${key}=${currentSection}; path=/; max-age=2592000`; // 30 days
        }

        function loadProgress() {
            const key = getCookieKey();
            const match = document.cookie.match(new RegExp(`(^| )${key}=([^;]+)`));
            return match ? Math.max(0, parseInt(match[2]) || 0) : 0;
        }

        // Find all comment nodes with "fold:break"
        function findFoldBreaks(element) {
            const breakNodes = [];
            const walker = document.createTreeWalker(
                element,
                NodeFilter.SHOW_COMMENT,
                {
                    acceptNode: function (node) {
                        return node.nodeValue.trim() === 'fold:break' ?
                            NodeFilter.FILTER_ACCEPT :
                            NodeFilter.FILTER_REJECT;
                    }
                }
            );

            let node;
            while (node = walker.nextNode()) {
                breakNodes.push(node);
            }

            return breakNodes;
        }

                // Section management
        function createSections(contentEl) {
            sections = [];

            console.log('Progressive Unfold: Looking for <!--fold:break --> comments...');

            // Get the raw HTML content but preserve original elements
            const htmlContent = contentEl.innerHTML;
            console.log('Progressive Unfold: Content length:', htmlContent.length);

            // Split by fold:break comments
            const foldBreakPattern = /<!--\s*fold:break\s*-->/gi;
            const htmlSections = htmlContent.split(foldBreakPattern);

            console.log('Progressive Unfold: Found', htmlSections.length, 'HTML sections');

            if (htmlSections.length <= 1) {
                console.log('Progressive Unfold: No fold:break comments found, disabling progressive unfold');
                return 0; // Return 0 to indicate no sections, so plugin does nothing
            }

            // Instead of recreating elements, map the existing elements to sections
            // by counting elements in each HTML section and grouping original elements accordingly
            const allOriginalElements = Array.from(contentEl.children);
            let elementIndex = 0;

            htmlSections.forEach((sectionHtml, idx) => {
                if (sectionHtml.trim() === '') return; // Skip empty sections

                // Count elements in this HTML section
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = sectionHtml.trim();
                const elementCount = tempDiv.children.length;

                // Map to original elements
                const sectionElements = allOriginalElements.slice(elementIndex, elementIndex + elementCount);
                if (sectionElements.length > 0) {
                    sections.push(sectionElements);
                    console.log(`Created section ${idx} with`, sectionElements.length, 'original elements');
                }

                elementIndex += elementCount;
            });

            // Fallback to original elements if no sections found
            if (sections.length === 0) {
                sections.push(Array.from(contentEl.children));
            }

            console.log('Progressive Unfold: Created', sections.length, 'sections total');
            return sections.length;
        }

        function showSection(sectionIndex) {
            if (sectionIndex < 0 || sectionIndex >= sections.length) {
                console.log('Invalid section index:', sectionIndex, 'max:', sections.length - 1);
                return;
            }

            console.log('Showing section', sectionIndex, 'of', sections.length);

            // Hide all sections first
            sections.forEach((section, idx) => {
                section.forEach(el => {
                    el.style.display = 'none';
                });
            });

            // Show sections up to and including the current one
            for (let i = 0; i <= sectionIndex; i++) {
                console.log('Revealing section', i);
                sections[i].forEach(el => {
                    el.style.display = '';
                });
            }

            currentSection = sectionIndex;
            updateNavigation();
            saveProgress();

            // Scroll to the start of the current section
            if (sections[sectionIndex] && sections[sectionIndex][0]) {
                sections[sectionIndex][0].scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }

        function createNavigation(contentEl) {
            // Remove existing navigation if it exists
            if (navContainer) {
                navContainer.remove();
            }

            navContainer = document.createElement('div');
            navContainer.className = 'progressive-unfold-nav';
            navContainer.style.cssText = `
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 20px;
        margin: 40px 0 20px 0;
        padding: 20px;
        border-top: 1px solid #eee;
        position: relative;
      `;

            prevBtn = document.createElement('button');
            prevBtn.innerHTML = '← Previous';
            prevBtn.style.cssText = `
        padding: 12px 24px;
        border: 1px solid #ddd;
        background: white;
        border-radius: 6px;
        cursor: pointer;
        font-size: 16px;
        font-weight: 500;
        color: #333;
        transition: all 0.2s ease;
      `;
            prevBtn.onmouseover = () => {
                if (!prevBtn.disabled) {
                    prevBtn.style.background = '#f5f5f5';
                    prevBtn.style.borderColor = '#ccc';
                }
            };
            prevBtn.onmouseout = () => {
                if (!prevBtn.disabled) {
                    prevBtn.style.background = 'white';
                    prevBtn.style.borderColor = '#ddd';
                }
            };
            prevBtn.onclick = () => {
                if (currentSection > 0) {
                    showSection(currentSection - 1);
                }
            };

            nextBtn = document.createElement('button');
            nextBtn.innerHTML = 'Next →';
            nextBtn.style.cssText = `
        padding: 12px 24px;
        border: 1px solid #ddd;
        background: white;
        border-radius: 6px;
        cursor: pointer;
        font-size: 16px;
        font-weight: 500;
        color: #333;
        transition: all 0.2s ease;
      `;
            nextBtn.onmouseover = () => {
                if (!nextBtn.disabled) {
                    nextBtn.style.background = '#f5f5f5';
                    nextBtn.style.borderColor = '#ccc';
                }
            };
            nextBtn.onmouseout = () => {
                if (!nextBtn.disabled) {
                    nextBtn.style.background = 'white';
                    nextBtn.style.borderColor = '#ddd';
                }
            };
            nextBtn.onclick = () => {
                if (currentSection < sections.length - 1) {
                    showSection(currentSection + 1);
                }
            };

            navContainer.appendChild(prevBtn);
            navContainer.appendChild(nextBtn);

            // Insert before the docsify-pagination container, then footer, then after content
            const paginationEl = document.querySelector('.docsify-pagination-container') || document.querySelector('[class*="pagination"]');
            const footerEl = document.querySelector('footer') || document.querySelector('.app-footer');

            if (paginationEl) {
                paginationEl.parentNode.insertBefore(navContainer, paginationEl);
            } else if (footerEl) {
                footerEl.parentNode.insertBefore(navContainer, footerEl);
            } else {
                // If no pagination or footer found, insert after the content element
                contentEl.parentNode.insertBefore(navContainer, contentEl.nextSibling);
            }

            updateNavigation();
        }

        function updateNavigation() {
            if (!prevBtn || !nextBtn) return;

            prevBtn.disabled = currentSection === 0;
            nextBtn.disabled = currentSection >= sections.length - 1;

            prevBtn.style.opacity = prevBtn.disabled ? '0.5' : '1';
            nextBtn.style.opacity = nextBtn.disabled ? '0.5' : '1';
            prevBtn.style.cursor = prevBtn.disabled ? 'not-allowed' : 'pointer';
            nextBtn.style.cursor = nextBtn.disabled ? 'not-allowed' : 'pointer';

            // Show section indicator
            if (sections.length > 1) {
                const indicator = navContainer.querySelector('.section-indicator') || document.createElement('div');
                indicator.className = 'section-indicator';
                indicator.style.cssText = `
          background: rgba(0, 0, 0, 0.7);
          color: white;
          padding: 6px 12px;
          border-radius: 4px;
          font-size: 14px;
          white-space: nowrap;
          margin: 0 10px;
        `;
                indicator.textContent = `Section ${currentSection + 1} of ${sections.length}`;

                if (!navContainer.querySelector('.section-indicator')) {
                    // Insert the indicator between the buttons
                    navContainer.insertBefore(indicator, nextBtn);
                }
            }
        }

        // Main initialization
        function initialize() {
            console.log('Progressive Unfold: Initializing...');

            const contentEl = document.querySelector('article#main') || document.querySelector('.content');
            if (!contentEl) {
                console.log('Progressive Unfold: No article#main or .content element found');
                return;
            }

            console.log('Progressive Unfold: Found content element:', contentEl.tagName, contentEl.id, 'with', contentEl.children.length, 'children');

            // Debug: Check for zoom-related classes
            const zoomImages = contentEl.querySelectorAll('.medium-zoom-image');
            console.log('Progressive Unfold: Found', zoomImages.length, 'images with zoom classes');

            // Debug: Check for images in general
            const allImages = contentEl.querySelectorAll('img');
            console.log('Progressive Unfold: Found', allImages.length, 'total images');

            const sectionCount = createSections(contentEl);
            if (sectionCount === 0) {
                console.log('Progressive Unfold: No sections created, aborting');
                return;
            }

            console.log('Progressive Unfold: Created', sectionCount, 'sections');

            // Only create navigation if we have multiple sections
            if (sectionCount > 1) {
                // Load saved progress
                const savedProgress = loadProgress();
                console.log('Progressive Unfold: Loaded saved progress:', savedProgress);

                // Create navigation
                createNavigation(contentEl);

                // Show initial section(s) - start with first section if no saved progress
                const initialSection = savedProgress > 0 ? Math.min(savedProgress, sectionCount - 1) : 0;
                console.log('Progressive Unfold: Starting with section', initialSection);
                showSection(initialSection);

                // Add keyboard navigation
                document.addEventListener('keydown', (e) => {
                    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

                    if (e.key === 'ArrowLeft' && currentSection > 0) {
                        e.preventDefault();
                        showSection(currentSection - 1);
                    } else if (e.key === 'ArrowRight' && currentSection < sections.length - 1) {
                        e.preventDefault();
                        showSection(currentSection + 1);
                    }
                });
            } else {
                console.log('Progressive Unfold: Only one section found, no navigation needed');
            }
        }

        // Hook into Docsify lifecycle
        hook.doneEach(() => {
            // Longer delay to ensure zoom plugin is fully initialized
            setTimeout(initialize, 1);
        });

        // Cleanup on route change
        hook.beforeEach(() => {
            if (navContainer) {
                navContainer.remove();
                navContainer = null;
            }
            sections = [];
            currentSection = 0;
        });
    }

    // Register the plugin
    if (typeof window !== 'undefined') {
        window.$docsify = window.$docsify || {};
        window.$docsify.plugins = (window.$docsify.plugins || []).concat([progressiveUnfoldPlugin]);
    }
})();
